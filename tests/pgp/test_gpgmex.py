import base64
import io
import os
import shutil
import stat
import tempfile
import unittest

from p3store.pgp import gpgmex


class PasswordFromFirstnameMixin(object):
    def password_callback(self, key, prev_was_bad):
        """
        Return "<firstname>2" as password.
        """
        first_name = key.gpgme_key.uids[0].name.split(' ', 1)[0]
        return '{}2'.format(first_name.lower())


class Gpgmex(PasswordFromFirstnameMixin, gpgmex.Gpgmex):
    """
    Gpgmex context object with adjusted password_callback.
    """
    pass


class HomedirTestCase(unittest.TestCase):
    """
    Test that the Gpgmex context object creates a safe location for the
    GPG homedir.
    """
    def test_new(self):
        # Check that the umask is touched.
        orig_umask = os.umask(0)
        try:
            # Think up a new temporary dirname.
            dirname = tempfile.mktemp()
            # Create it, we should be fast enough.
            Gpgmex(dirname)
            # Check it.
            info = os.stat(dirname)
            self.assertEqual(stat.S_IMODE(info.st_mode), 0o700)
        finally:
            os.umask(orig_umask)
            if os.path.exists(dirname):
                os.rmdir(dirname)

    def test_existing_good_perms(self):
        # Create new temporary dir.
        dirname = tempfile.mkdtemp()  # should be 0o700 already
        self.assertTrue(os.path.exists(dirname))
        try:
            # New context, don't touch the dir.
            Gpgmex(dirname)
            # Check it.
            info = os.stat(dirname)
            self.assertEqual(stat.S_IMODE(info.st_mode), 0o700)
        finally:
            os.rmdir(dirname)

    def test_existing_bad_perms(self):
        # Create new temporary dir.
        dirname = tempfile.mkdtemp()  # should be 0o700 already
        # Alter perms.
        os.chmod(dirname, 0o710)
        try:
            # New context, don't touch the dir.
            self.assertRaises(FileExistsError, Gpgmex, dirname)
        finally:
            os.rmdir(dirname)

    def test_destroy_homedir(self):
        # Think up a new temporary dirname.
        dirname = tempfile.mktemp()
        try:
            # Create it, we should be fast enough.
            gpg = Gpgmex(dirname)
            # It exists.
            self.assertTrue(os.path.exists(dirname))
            # Add some garbage to it.
            with open(os.path.join(dirname, 'hello'), 'w') as fh:
                fh.write('world\n')
            # Destroy it.
            gpg.destroy_homedir()
            # Check it.
            self.assertFalse(os.path.exists(dirname))
        finally:
            try:
                shutil.rmtree(dirname)
            except FileNotFoundError:
                pass


class EncryptAndDecryptTestCase(unittest.TestCase):
    def test_encrypt(self):
        gpg = Gpgmex()
        try:
            # The fingerprint of <walter-rsa-rsa@example.com>.
            key = gpg.get_key_by_id('E08B48D4923B68D03CE8274DAF386C4BFA33BF5B')
            # Create data and output storage.
            infile = io.BytesIO(b'Hello World!\n')
            outfile = io.BytesIO()
            # Encrypt.
            gpg.encrypt(infile, outfile, [key])
            data = outfile.read()
            self.assertNotIn(b'Hello World', data)
            self.assertTrue(len(data) > 50)
        finally:
            gpg.destroy_homedir()

    def test_decrypt(self):
        data = base64.b64decode(b'''
            hIwD5Bvqd+L4q4IBBACliz39QQ12sXYr7bISSnMZVlcLJ5+BEmFstgtj+aX7
            +QnOAZYKfPLNCZFX6Lfz3EYr4xgbAZu2wPktlzGinUN61MUGvFG2PPsl4l1T
            hZZxkDGIhaWCSlhu9KRCQRS58GV35C8mH972h1MEkncGeKzGaw1G71V5WWgZ
            3OAidcUhKdJLAdJxCyN+EoUwEIrtU94USVu39t/cCDUFzZ5C7hjOH+mk6qZ4
            vBjryyqG62xWXeUhQzBrXPvAH2rVLMoR4bulb81YGIPmqO5XRph4''')

        # Drop GPG agent support, if enabled. We want our own password
        # entry.
        os.environ.pop('GPG_AGENT_INFO')

        gpg = Gpgmex()
        try:
            # Load data and output storage.
            infile = io.BytesIO(data)
            outfile = io.BytesIO()
            # Decrypt.
            gpg.decrypt(infile, outfile)
            data = outfile.read()
            self.assertEqual(data, b'Hello World!\n')
        finally:
            gpg.destroy_homedir()
