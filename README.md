
## Listeners
#### bot is ready
    - init status and activity a bot
    - delete postgres tables
    - create postgres tables
    - guild initialize
        - insert guild in db
        - insert members in db
        - insert user profiles in db
        - insert roles in db
        - insert channels in db
        - insert invites in db
        - insert permissions in db
#### bot adds a new guild
    - guild initialize
#### bot remove from a guild
    - notice
#### send a message in a chat
    - update counter messages user and channel and cash user
#### change message
    - send embed about change message
#### change delete
    - send embed about change message
#### user join in a guild
    - insert members in db
    - insert user profiles in db
    - add roles if role saver true
    - insert invites in db
    - send embed about user in a log chat
    - rename user count voice (use dict names)
#### user remove in a guild
    - insert user roles in db
    - send embed about user in a log chat
    - rename user count voice (use dict names)        
#### user create invite in a guild
    - insert_invite_in_db_invites
#### change user voice status
    - update counter minutes user and channel and cash user

## Commands
change prefix
#### clear
    - clear message from a chat
#### embed
    - send embed in a chat
#### role
    - send list users with goal role
#### info_user
    - send in chat info about user
#### top_chat_users
    - send in chat list top users by messages
#### top_voice_users
    - send in chat list top users by minutes    
#### top_chat_channels
    - send in chat list top channels by messages
#### top_voice_channels
    - send in chat list top channels by minutes    
#### top_invites
    - send in chat list top users by coins
#### top_coins
    - send in chat list top users by invites
#### guild
    - send in chat info about guild
#### day
    - send in chat day statistics
#### help
    - list commands
    

## Utils
    - send in chat day statistics (background loop task)
    - check permission dor use command
