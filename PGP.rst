# A few notes about subkeys:
#
# -----------------------------------------------------------------------------
# From: http://wiki.debian.org/subkeys
#
# > GnuPG actually uses a signing-only key as the master key, and creates an
# > encryption subkey automatically. Without a subkey for encryption, you
# > can't have encrypted e-mails with GnuPG at all. Debian requires you to
# > have the encryption subkey so that certain kinds of things can be e-mailed
# > to you safely, such as the initial password for your debian.org shell
# > account.
# ...
# > You should keep your private master key very, very safe. However, keeping
# > all your keys extremely safe is inconvenient: every time you need to sign
# > a new package upload, you need to copy the packages onto suitable portable
# > media, go into your sub-basement, prove to the armed guards that you're
# > you by using several methods of biometric and other identification, go
# > through a deadly maze, feed the guard dogs the right kind of meat, and
# > then finally open the safe, get out the signing laptop, and sign they
# > packages. Then do the reverse to get back up to your Internet connection
# > for uploading the packages.
# >
# > Subkeys make this easier: you create a subkey for signing, and another for
# > encryption, and keep those on your main computer. You publish the subkeys
# > on the normal keyservers, and everyone else will use them instead of the
# > master keys, with one exception. Likewise, you will use the master keys
# > only in exceptional circumstances.
#
# -----------------------------------------------------------------------------
# From: http://serverfault.com/questions/397973/
#              gpg-why-am-i-encrypting-with-subkey-instead-of-primary-key
#
# > If you look into the details of the math of public-key encryption, you will
# > discover that signing and decrypting are actually identical operations.
# > Thus in a naive implementation it is possible to trick somebody into
# > decrypting a message by asking them to sign it.
# >
# > Several things are done in practice to guard against this. The most obvious
# > is that you never sign an actual message, instead you sign a secure hash of
# > the message. Less obviously, but just to be extra safe, you use different
# > keys for signing and encrypting.
#
# -----------------------------------------------------------------------------
# From: http://lavica.fesb.hr/cgi-bin/info2html?(gpgme)Key%20Management
#
# > The first subkey in the linked list is also called the primary key.
#
# -----------------------------------------------------------------------------
# The Key object that we get below, generally holds two subkeys:
# >>> [(i.can_sign, i.can_encrypt, i.pubkey_algo) for i in k.subkeys]
# [(True, False, 17), (False, True, 16)]
#
# (Where 17 is PUBKEY_ALGO_DSA and 16 is PUBKEY_ALGO_ELGAMAL_E.)


