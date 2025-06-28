# song share
Share your favorite songs, and see what others are listening to.

<br />
Current state of the application: <br />
- The user can create an account and log in to the application.<br />
- The user can add, edit, and delete posts and songs.<br />
- The user sees the posts and songs added to the application.<br />
- The user can search for songs by keyword.<br />
- The user can select one or more classifications for a data item. <br />
- The user can send comments to another user's post, which will be displayed in the application.<br />
- The user page shows statistics and user-added data items. <br />

<br />
To run the application, first:

`python3 -m venv venv`<br />
`source venv/bin/activate`<br />
`pip install flask`<br />

then:

`flask init-db`

finally:

`flask run`

If there is an error, try first:

`sqlite3 database.db < schema.sql`
