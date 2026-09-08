# Inputs and injection

Most web attacks come down to one mistake: the server took data from a stranger
and treated part of it as an instruction. Injection is the name for that
mistake, and understanding it defensively means learning to see the exact spot
where user-supplied text crosses into a database query, a shell command, or a
page other people view. That boundary is where trust is either kept or lost.

Everything here runs only against Range targets you own: a Rocky 9 lab app,
built to be weak on purpose, that you start yourself with `pridwen enter rocky`.
You never send these inputs to an app you do not control. On a real job the same
eye tells you which parameters in your own code reach a query unescaped, which
is the difference between a safe form and a breach.

## Words you'll meet

- **input**: any value that comes from outside the program, such as a URL query parameter, a form field, or a header.
- **parameter**: a named value in a URL after the `?`, like `id=1` in `/item?id=1`.
- **query**: the sentence a program sends to a database to ask for or change data, written in SQL.
- **SQL injection**: an attack where input is glued into a SQL query so the input changes what the query does.
- **cross-site scripting (XSS)**: an attack where input is placed into a page so a victim's browser runs it as code.
- **parameterised query**: a query where values travel in a separate slot from the SQL text, so input can never become SQL.
- **URL-encoding**: writing characters that have meaning in a URL as `%NN`, so a space is `%20` and a single quote is `%27`.

## How it works

Start with the boundary drawn clearly. A normal request sends a value the app
expects, and the app returns the matching record:

```
{user}@{host}:~$ curl -s 'http://range-app/item?id=1'
{"id":1,"name":"widget","price":"4.00"}
```

The `-s` flag is silent (no progress meter). The parameter is `id=1`, and the
reply is one JSON record: `id` 1, a name, a price. That is the app working as
intended, with the input used only as data.

Now the probe. On the weak lab app, you send input shaped like SQL to test
whether the value is being pasted into the query text instead of kept as data:

```
{user}@{host}:~$ curl -s "http://range-app/item?id=1%27"
{"error":"unterminated quoted string at or near \"'\""}
```

Read that back. `%27` is a URL-encoded single quote; the app decoded it and
dropped a bare `'` into its SQL, which broke the query's own syntax, and the
database complained. That error message is the finding: it proves the input
reached the SQL text, which is exactly the door a parameterised query closes.
XSS is the same mistake pointed at a page instead of a query, where input is
written into HTML and the victim's browser runs it.

The defence is one principle said many ways: never mix data with code. A
parameterised query sends the SQL and the values in separate slots, so `id`
can hold `1'` or anything else and it is still only a value. Output encoding
does the same for HTML, turning `<` into `&lt;` so text can never become a tag.
On the Range you run the fixed version and watch the same probe come back as an
ordinary "not found" instead of a database error, and each attempt is a logged
request a defender can count later.

## When it goes wrong

`{"error":"unterminated quoted string..."}` on the weak app is the point of the
exercise, not a failure: it is the database telling you your input became part of
its sentence. On a fixed app the same input returns a normal empty result.

`curl: (3) URL using bad/illegal format` means the quoting on your side is wrong,
usually an unescaped character in the shell. Wrap the whole URL in single quotes
and URL-encode the special characters (`'` becomes `%27`, a space becomes `%20`).

`curl: (7) Failed to connect` means the lab app is not listening; start the
Range target first. Run `pridwen explain curl` if a flag in the command is the
part you are unsure about.

## Try it

1. Start the Range lab app with `pridwen enter rocky` and note its name.
2. Send a normal request such as `curl -s 'http://range-app/item?id=1'` and read the record it returns.
3. Send `id=1%27` and read the error; explain in one sentence why it proves the input reached the SQL.
4. Run the app's fixed version and send the same probe; note that it no longer errors.
5. State the one rule that connects SQL injection and cross-site scripting.

## Remember

- Injection happens when input crosses from data into code, whether that code is SQL for a database or HTML for a browser.
- A database error from a single quote is the sign that input reached the query text; a parameterised query keeps values in a separate slot so it never can.
- The rule behind every fix is the same: never mix data with code, and encode or parameterise at every boundary input crosses.
