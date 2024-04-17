Help & Support
==============

Support Server
--------------

Ask your questions in #support_aaa3a-cogs on the `cogs support server <https://discord.gg/red-cog-support-240154543684321280>`__

Common Questions
----------------

**Dashboard cog is loaded, and webserver is up, but it isn't showing my bot's info.**

-  Did you start the bot with the RPC flag?
-  If you started the bot with the ``--rpc-port`` flag, did you provide the same port to ``reddash``\ command when starting the webserver? Vice versa?
-  Have you set the redirect and secret in the cog's settings?
-  Have you tried reloading the Dashboard cog/restarting the webserver?
-  Have you tried updating the Dashboard cog and the webserver itself?
-  Have you tried restarting the bot?

**My browser said the website take too much time to answer or a similar error.**

Your firewall is maybe not configured to accept the port Dashboard is listening for, if you are on Linux, run ``sudo ufw allow <webport>`` (Default is 42356). If you are on Windows, type ``Firewall`` in your search bar and add a new rule.
