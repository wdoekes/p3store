import os
from getpass import getpass
from shutil import rmtree
from stat import S_IMODE
from time import time

from gpgme import ERR_CANCELED, Context, GpgmeError  # req: python-gpgme


class GpgmexKey(object):
    """
    Wrapper around the gpgme key object.
    """
    def __init__(self, gpgme_key):
        self.gpgme_key = gpgme_key
        self.check()

    def check(self):
        if self.gpgme_key.expired:
            raise ValueError('{} is expired'.format(self))
        elif (self.gpgme_key.invalid or self.gpgme_key.revoked or
              self.gpgme_key.disabled):
            raise ValueError('{} is invalid/revoked/disabled'.format(self))
        elif not self.gpgme_key.can_encrypt:
            # can_encrypt is also set to false if it's e.g. expired.
            raise ValueError('{} is unusable'.format(self))

        # Find right subkey and check if expiry is nigh.
        for subkey in self.gpgme_key.subkeys:
            if not (subkey.expired or subkey.invalid or subkey.revoked or
                    subkey.disabled or not subkey.can_encrypt):
                break
        if subkey.expires and float(subkey.expires - time()) / 86400.0 < 200:
            # Send out a warning that this key is about to expire. I'm not
            # sure what the implications of expired keys are, but let's prepare
            # for the worst and warn the user at an early stage.
            raise ValueError('{} encryption subkey expires in {} days'.format(
                self, float(subkey.expires - time()) / 86400.0))

    def algo_to_str(self, pubkey_algo):
        if pubkey_algo == 1:
            return 'RSA'
        elif pubkey_algo == 16:
            return 'ELG-E'
        elif pubkey_algo == 17:
            return 'DSA'
        raise NotImplementedError('algo {}'.format(pubkey_algo))

    def subkey_to_str(self, gpgme_subkey):
        properties = [self.algo_to_str(gpgme_subkey.pubkey_algo)]
        if gpgme_subkey.can_sign:
            properties.append('sign')
        if gpgme_subkey.can_encrypt:
            properties.append('enc')
        if gpgme_subkey.secret:
            properties.append('secret')
        if gpgme_subkey.expired:
            properties.append('expired')
        return '{key_id}({properties})'.format(
            key_id=gpgme_subkey.keyid, properties=','.join(properties))

    def __str__(self):
        email = self.gpgme_key.uids[0].email.lower()
        return '{primary_key} <{email}> [{keys}]'.format(
            primary_key=self.gpgme_key.subkeys[0].keyid[-8:],
            email=email, keys=', '.join(
                self.subkey_to_str(i) for i in self.gpgme_key.subkeys))


class Gpgmex(object):
    """
    Gpgme context object. Holds convenience functions.

    If you're running a password caching agent, you'll have the
    GPG_AGENT_INFO environment variable set. Unset it to disable the
    agent.
    """
    def __init__(self, homedir=None):
        # Ensure that there is a homedir for GNUPGHOME.
        if not homedir:
            homedir = '/tmp/p3store-gpg-{}'.format(os.getuid())
        self._homedir = homedir
        self.ensure_homedir()

        # Init a GPG context.
        self._gpgme = Context()
        self._gpgme.passphrase_cb = self._password_callback
        # No ascii armor stuff. We'll juggle some base64 around
        # ourselves.
        self._gpgme.armor = False

    def destroy_homedir(self):
        # Clean up our act. This should be called from tests, but is not
        # necessary when using it normally. There is nothing wrong with
        # a bit of cache.
        rmtree(self._homedir)
        self._homedir = None
        self._gpgme = None

    def ensure_homedir(self):
        orig_umask = os.umask(0o077)
        try:
            os.makedirs(self._homedir)
        except FileExistsError:  # OSError.errno=17
            info = os.stat(self._homedir)
            if S_IMODE(info.st_mode) != 0o700:
                raise
        finally:
            os.umask(orig_umask)

    def get_key_by_id(self, key_id):
        """
        Get a GpgmexKey wrapped key. Pass key_id as uppercase radix16.
        """
        # "If [PARAM2] is 1, only private keys will be returned."
        gpgme_key = self._gpgme.get_key(key_id, 0)
        return GpgmexKey(gpgme_key)

    def encrypt(self, infile, outfile, public_keys):
        """
        Encrypt infile to outfile, using the supplied public keys. The
        GPG internals will take the encryption subkey from the supplied
        keys.

        Note that for p3store purposes, we'll probably encrypt to a
        single user, then take the first PGP blob, decrypt the
        symmetric key and re-encrypt it for several users using
        python-pgp: that way we won't need to import foreign public
        keys into the user's GNUPGHOME.
        """
        assert hasattr(infile, 'read')
        assert hasattr(outfile, 'write')
        assert public_keys

        self._gpgme.encrypt([i.gpgme_key for i in public_keys],
                            1, infile, outfile)
        # length = output.tell()
        outfile.seek(0)

    def decrypt(self, infile, outfile):
        """
        Decrypt infile to outfile. We let the GPG internal handle the
        private key match.
        """
        assert hasattr(infile, 'read')
        assert hasattr(outfile, 'write')

        try:
            self._gpgme.decrypt(infile, outfile)
        except GpgmeError as e:
            # If you press ^C during passphrase input.
            #   gpgme.GpgmeError: (7, 58, u'No data')
            # If the decryption failed (badly encrypted, secret key missing)
            #   gpgme.GpgmeError: (7, 152, u'Decryption failed')
            # If the password callback raised an error.
            #   gpgme.GpgmeError: (7, 32779, u'Bad file descriptor')
            if e.args[0] == 7:
                if e.args[1] == 11:
                    raise ValueError('Bad password')
                if e.args[1] == 152:
                    raise ValueError('Bad private key')
            raise

        # length = output.tell()
        outfile.seek(0)

    def password_callback(self, key, prev_was_bad):
        """
        Really basic password callback that doesn't do any caching.

        Gnome keyring already takes care of the key access if you're
        running the GPG agent. If you cancel the GPG popup, you get
        this callback instead. Subclass if you want special behaviour.
        """
        return getpass('Enter passphrase for {}: '.format(key))

    def _password_callback(self, uid_hint, passphrase_info, prev_was_bad, fd):
        """
        The password callback is called from the gpgme context if the
        GPG_AGENT is unavailable and a password is required.

        This method wraps the password callback.
        """
        # The argument uid_hint might contain a string that gives an
        # indication for which user ID the passphrase is required. If
        # this is not available, or not applicable (in the case of
        # symmetric encryption, for example), uid_hint will be NULL.
        #
        #     E41BEA77E2F8AB82 Walter (Example) <walter@example.com>
        #     ^-- encryptkey_id  ^-- name ^-- comment  ^-- email
        #
        # The argument passphrase_info, if not NULL, will give further
        # information about the context in which the passphrase is
        # required. This information is engine and operation specific.
        #
        #    E41BEA77E2F8AB82 AF386C4BFA33BF5B 1 0
        #    ^-- encryptkey_id  ^-- mainkey_id
        #
        # If this is the repeated attempt to get the passphrase,
        # because previous attempts failed, then prev_was_bad is 1,
        # otherwise it will be 0.

        if uid_hint:
            encryptkey_id = uid_hint.split(' ', 1)[0]
            key = self.get_key_by_id(encryptkey_id)
        prev_was_bad = bool(prev_was_bad)

        # Get the password from the callback.
        try:
            password = self.password_callback(key, prev_was_bad)
            assert isinstance(password, str)
            password = password.encode('utf-8')
        except KeyboardInterrupt:
            # For some reason, we return 'No data' next..
            pass
        except Exception:
            import traceback
            traceback.print_exc()
        else:
            # Writing empty passwords too, because the close below is so
            # drastic that we wouldn't get a second try.
            os.write(fd, password + b'\n')
            return 0

        # > The user must write the passphrase, followed by a newline
        # > character, to the file descriptor fd. If the user returns 0
        # > indicating success, the user must at least write a newline
        # > character before returning from the callback.
        # >
        # > If an error occurs, return the corresponding gpgme_error_t value.
        # > You can use the error code GPG_ERR_CANCELED to abort the operation.
        # > Otherwise, return 0.
        #
        # But that doesn't work. We must always write a newline, or the thing
        # hangs. Returning 0 or ERR_CANCELED doesn't seem to make any
        # difference. So, instead, we close() the fd. That will make for a
        # quicker abort: 'Bad file descriptor'
        os.close(fd)
        return ERR_CANCELED
