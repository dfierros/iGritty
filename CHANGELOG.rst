=========
Changelog
=========

Version 1.1.0
===========
- Fixing scheduled trains not working properly due to database reloads
  - Resolves https://github.com/dfierros/iGritty/issues/3
- Reworked `!train`
  - Users can now provide a custom train message
  - Polls on trains are now optional
- Reworked `!schedule_train`
  - Added support for custom train message & optional poll (from `!train`) 

Version 1.0.1
===========

- Fixing `!train` lead time being negative rather than positive
  - Resolves https://github.com/dfierros/iGritty/issues/1 

Version 1.0.0
===========

- Initial Release
- Added Simple bot
- Added persistent database
- Added support for the following train-related commands:
  - `!train` 
  - `!schedule_train` 
  - `!upcoming_trains` 
  - `!cancel_train` 
- Added support for the following bot command:
  - `!version` 
