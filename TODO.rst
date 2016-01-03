TODO list
=========

Client
------

* Design fool-proof pstore client interface for the most basic commands::

    p3store --config ~/.p3storerc --user <whoami> --server <server1> --server <server2> \
            [<namespace>::]<objname> [<property>] 

    # Get global info.
    p3store myserver.tld [-s]  # or search if -s is supplied
    # Get property.
    p3store myserver.tld --get someproperty.txt
    p3store myserver.tld --fget someproperty.txt local-someproperty.txt
    # Set property (encrypted).
    p3store myserver.tld --set someproperty.txt   # will do password-style prompts?
    p3store myserver.tld --fset someproperty.txt local-someproperty.txt  # optionally use - for stdin?
    # Set property in plaintext.
    p3store myserver.tld --plain someproperty.txt
    p3store myserver.tld --fplain someproperty.txt local-someproperty.txt
    # Set multiple properties at once:
    p3store myserver.tld set someproperty.txt -

    # If object does not exist, add --create. Then --grant <@group|user> is mandatory.
    p3store myserver.tld --create --grant @beheer
    # Alter perms. Use "least surprise" so --grant johnny does not mean that we
    # revoke @beheer automatically.
    p3store myserver.tld --alter --grant johnny,@users --revoke @beheer

    # Add new object. (FUTURE!)
    p3store myserver.tld create [template ssh]
    # ^-- client-side templates for now?
    # defines that it will ask for all properties as found in ssh template


Server
------

* Slash escaping problem?
  - double escaping?
  - http://codeinthehole.com/writing/django-nginx-wsgi-and-encoded-slashes/

* Add auth to the server. Falcon middleware?

* Begin with filesystem backend. Improve to git-backend. Fairly trivial
  subclass?


Not Doing Now
-------------

* Add pstore-style gpgme backend, for encryption speed and security? Only use
  python-pgp for splitting up the packets?
  ... or perhaps we do want it, so we don't need to trust python-pgp security
  as much: we won't need to update GPGHOME to a different path, since we won't
  have GnuPG add the other users' keys: we'll do the granting through
  python-pgp instead.

* Re-create the python-pgp pub/priv keys so they don't expire? Also rename
  from walter@example.com to walter-rsa-rsa@example.com.
