## PyDD

A hybrid algorithmic debugger and program synthesis engine for Python 

#### Repository structure

```bash
├── app.py
├── ast_transformer.py
├── coverage.dat
├── coverage.py
├── debugging_strategy.py
├── etnode.py
├── event.py
├── execution_tree.py
├── frontend
│   ├── package.json
│   ├── package-lock.json
│   ├── public
│   ├── README.md
│   └── src
│       ├── App.js
│       ├── App.test.js
│       ├── ColorModeSwitcher.js
│       ├── index.js
│       ├── Logo.js
│       ├── logo.svg
│       ├── reportWebVitals.js
│       ├── serviceWorker.js
│       ├── setupTests.js
│       ├── test-utils.js
│       ├── TreeView.js
│       └── TreeViewMenu.js
├── grammar.py
├── oracle.py
├── program_repairer.py
├── pydd.py
├── pydd_repl.py
├── query.py
├── README.md
├── server.py
├── trace.dat
├── trace_iterator.py
└── tracer.py
```

#### Installation

In the frontend directory run:
#### `npm install`

Install all dependencies for client-side application.

In the parent (base) directory run:
#### `pip install tornado dill astor pygments rich astor astunparse textwrap`


#### Usage:

`./app.py -f ~/Desktop/bug1.py -d heaviest-first -pr bus`

##### CLI

```md
usage: app.py [options]
app.py: error: the following arguments are required: -f, -d, -pr

OPTIONS
-f 	target file
-i 	enable interactive debugging
-w 	enable web mode
-d 	debugging strategy
-pr	program repair strategy
-t 	trace file
-c 	coverage file
```

#### Debug commands

_class_ PyDDRepl. **do_next**(args)

_class_ PyDDRepl. **do_prev**(args)

_class_ PyDDRepl. **do_print**(args)

_class_ PyDDRepl. **do_break**(args)

_class_ PyDDRepl. **do_watch**(args)

_class_ PyDDRepl. **do_remove**(args)

_class_ PyDDRepl. **do_continue**(args)

_class_ PyDDRepl. **do_exit**(args)

_class_ PyDDRepl. **do_list**(args)

_class_ PyDDRepl. **do_repair**(args)

#### Debugging strategies

_class_ DebuggingStrategy. **single_stepping**

_class_ DebuggingStrategy. **top_down**

_class_ DebuggingStrategy. **heaviest_first**

_class_ DebuggingStrategy. **divide_and_query**

#### Program repair strategies

_class_ Grammar. **bus**

_class_ Grammar. **bfs**

_class_ Grammar. **dfs**

