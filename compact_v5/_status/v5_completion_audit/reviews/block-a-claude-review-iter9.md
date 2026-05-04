NO_VERDICT / HANDOFF_FAILED_AUTH_COMMAND

Claude did not produce review stdout. The iter9 command failed before review
because PowerShell split `--setting-sources user,project,local` into separate
arguments and Claude reported:

`Error processing --setting-sources: Invalid setting source: user project local. Valid options are: user, project, local`
