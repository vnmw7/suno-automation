git branch --merged | Where-Object {$_ -notmatch 'main|master'} | ForEach-Object { git branch -d $_.Trim() }
