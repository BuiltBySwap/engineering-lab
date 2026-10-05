# Coroutines under the hood

## The problem
Threads are expensive (~1 MB of stack each) and mostly wait. Callbacks free the thread but nest. ___ (one line in your words)

## The idea: a kitchen
Threads are cooks, coroutines are order cards with a bookmark, a dispatcher is the head chef.
`suspend` means: put the card down with its bookmark and take another one.

## What the compiler does
`suspend` adds a hidden `Continuation` parameter and rewrites the function into a state machine:
a `label` (bookmark) plus saved local variables, stored in an object on the heap.
A function with N suspension points has N + 1 states.

## What I measured (11-core Mac)
| Experiment | Result |
|---|---|
| 2 × `delay(1000)` on one thread | 1013 ms |
| 2 × `Thread.sleep(1000)` on one thread | 2013 ms |
| 22 blocking tasks on `Default` (11 threads) | 2011 ms |
| 22 blocking tasks on `IO` | 1011 ms |
| 11 CPU loops, then 33 CPU loops on 11 cores | 1008 ms, then 3003 ms |

Rule: time ≈ ceil(tasks ÷ threads) × time each task holds its thread.

## Rules I'll use
- Never block `Main` or `Default`; use a suspend API or `withContext(Dispatchers.IO)`.
- A suspend function should be main-safe: it picks its own dispatcher.
- ___ (one more rule, in your words)

## Where I used it
___ (a ViewModel or repository from your Amaha or Kaizen work, in one line)
