# Implementation Loop

For each port boundary:

1. Record an observable failing test or device scenario.
2. Apply the smallest production change that addresses the confirmed cause.
3. Run the focused test, then the relevant build.
4. Exercise the result on the connected physical iPhone.
5. Update the contract evidence and create a checkpoint commit only while GREEN.

No runtime workaround is accepted without a regression test or a reproducible device check.
