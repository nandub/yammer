Gale is an obscure public key cryptography chat system.  Installing and running Gale for the first time is immensely complicated because of the public key authentication framework.

Yammer is a Web UI written in Python on the Webware framework; it
makes it trivial to get started using Gale: you just create a user
account and converse with the cranky denizens.  Yammer takes care of
key generation and distribution.  All public conversation is stored in
its database, as are your private messages, which are sent encrypted
over the wire and are readable only by you.

Yammer also provides web services that allow other Gale clients to use
it to create user accounts.





