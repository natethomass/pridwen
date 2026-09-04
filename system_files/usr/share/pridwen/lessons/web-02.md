# Inputs and injection

Most web attacks come down to input the server trusted when it should not.
Understanding injection defensively means seeing where user-supplied data crosses
into a query, a command, or a page, because that boundary is where trust is won or
lost.

The classic examples are SQL injection, where input becomes part of a database
query, and cross-site scripting, where input becomes part of a page others view.
On a Range target with a deliberately weak app, you can watch a crafted parameter
change a query's meaning, and then see how parameterised queries and output
encoding shut it down.

```
$ curl 'http://web-01/item?id=1'          # normal
$ curl 'http://web-01/item?id=1%20OR%201=1'  # probing whether input is trusted
```

The defence is a single principle stated many ways: never mix data with code.
Parameterised queries keep input out of SQL syntax, output encoding keeps it out
of HTML, and validation rejects what does not fit. On the Range you attack the
weak version to see the failure, then run the fixed version to see the principle
hold. The point is not the payload but the boundary, and learning to spot every
place untrusted input crosses it.

## Try it

1. On a Range app built for it, send a normal request and read the response.
2. Send a probing input and observe whether the app trusts it.
3. Compare the behaviour against a version using parameterised queries.
4. Explain the rule that connects SQL injection and cross-site scripting.
