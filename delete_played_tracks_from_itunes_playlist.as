-- remove tracks from playlists "ib" and "ib2" that have played counts
-- other than 0
--
-- This can be used to auto-prune playlists that should only contain unplayed
-- tracks.
--
-- After execution it will display a dialog showing the naems of tracks that
-- were removed.
--
tell application "iTunes"
  set output to ""
  repeat with pl in {"ib"} & {"ib2"} & {"ib4"}
    set toDelete to {}
    repeat with t in tracks of playlist pl
      if played count of t is not 0 then
        set toDelete to toDelete & {name of t as text}
      end if
    end repeat
    repeat with tname in toDelete
      repeat with t in (every track of (playlist pl) whose name is tname)
        tell playlist pl to delete contents of t
        set output to output & quoted form of (tname) & "
"
      end repeat
    end repeat
  end repeat
end tell
display dialog output

