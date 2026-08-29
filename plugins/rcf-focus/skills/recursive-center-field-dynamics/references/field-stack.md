# Recursive field stack

Read this reference when a required address opens a child field or when exploration is stalling.

## Expansion contract

Every child frame records:

- one parent field and one parent address;
- why the parent opened it;
- the required child output;
- the child closure requirement;
- the form of the parent return.

The child may preserve multiple centers in its panorama, but its local projection selects one current center. Global depth increases by exactly one.

## Fold

Fold compresses evidence, conclusion, outputs, assumptions, peer effects, latent residuals, active residuals, and a reopen address. Selected-center closure and complete-field closure remain separate.

## Unwind

After a child fold, unwind one frame. Realize the parent address only when the complete child field closed. Otherwise return the open interface and keep the parent address unrealized.

Unwind to the nearest ancestor that can make a different decision when any of these holds:

- two consecutive passes add no task-relevant evidence;
- the same addresses and hypothesis recur;
- the child no longer changes the parent interface;
- the required output cannot be produced in the current boundary;
- another center or branch must be selected at an ancestor.

Do not drill deeper merely to make the field appear complete. Preserve the stalled child as evidence and a reopen point.
