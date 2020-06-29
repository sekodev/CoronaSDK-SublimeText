#
# Sublime Text plugin to support Solar2D Editor
#
# Copyright (c) 2013 Corona Labs Inc. A mobile development software company. All rights reserved.
#
# MIT License - see https://raw.github.com/coronalabs/CoronaSDK-SublimeText/master/LICENSE

import sublime
import sublime_plugin

try:
  from . import _corona_utils  # P3
except:
  import _corona_utils  # P2


class ToggleBuildPanelCommand(sublime_plugin.WindowCommand):

  def __init__(self, window):
    self.window = window
    self.output_panel = None

  def run(self):
    # The output panel content is cleared anytime "get_output_panel()" is called
    # so we minimize how often we do that
    if self.output_panel is None:
      self.output_panel = self.window.get_output_panel("exec")
    if self.output_panel.window():
      self.window.run_command("hide_panel", {"panel": "output.exec"})
    else:
      self.window.run_command("show_panel", {"panel": "output.exec"})

  def description(self):
    if self.output_panel is None:
      self.output_panel = self.window.get_output_panel("exec")
    if self.output_panel.window():
      return "Hide Build Panel"
    else:
      return "Show Build Panel"

class ClearOutputPanelCommand(sublime_plugin.WindowCommand):

  def __init__(self, window):
    self.window = window
    self.output_panel = None

  def is_enabled(self):
    if self.output_panel is None:
      self.output_panel = self.window.get_output_panel("exec")
    return self.output_panel.window() is not None

  def run(self):
    # The output panel content is cleared anytime "get_output_panel()" is called
    self.window.get_output_panel("exec")


class RunProjectCommand(sublime_plugin.WindowCommand):

  # find a main.lua file to start the Simulator with or failing that, any open Lua
  # file we can use as a place to start looking for a main.lua
  def findLuaFile(self):
    filename = None
    if self.window.active_view():
      filename = self.window.active_view().file_name()
    if filename is None or not filename.endswith(".lua"):
      filename = None
      # No current .lua file, see if we have one open
      for view in self.window.views():
        if view.file_name() and view.file_name().endswith(".lua"):
          filename = view.file_name()
          break
    return filename

  def is_enabled(self):
    return self.findLuaFile() is not None

  def run(self):
    cmd = []

    filename = self.findLuaFile()

    if filename is None:
      sublime.error_message("Can't find an open '.lua' file to determine the location of 'main.lua'")
      return
    mainlua = _corona_utils.ResolveMainLua(filename)
    if mainlua is None:
      sublime.error_message("Can't locate 'main.lua' for this project (try opening it in an editor tab)")
      return

    simulator_path, simulator_flags, simulator_version = _corona_utils.GetSimulatorCmd(mainlua)

    print(_corona_utils.PACKAGE_NAME + ": Running: " + str(cmd))

    # Exit the debugger if it's running
    self.window.run_command("corona_debugger", {"cmd": "exit"})

    # Save our changes before we run
    self.window.run_command("save_all")

    # Supplying the "file_regex" allows users to double-click errors and warnings in the
    # build panel and go to that point in the code
    if sublime.platform() == 'osx':
      # On OS X, running the command as a string argument to the shell allows
      # the "corona_sdk_simulator_show_console" option to work (otherwise
      # stdout gets screwed up and hangs)
      try:  # py3
          from shlex import quote
      except ImportError:  # py2
          from pipes import quote

      cmd = [ simulator_path ]
      cmd += simulator_flags
      cmd.append(mainlua)
      # quote command arguments
      cmdStr = ' '.join([ quote(arg) for arg in cmd ])
      self.window.run_command('exec', {'cmd': cmdStr, "file_regex": "^(?:ERROR: |WARNING: )*(/[^:]*):([0-9]+):([0-9]?)(.*)$", "shell": "/bin/sh"})
    else: # windows
      cmd = [ simulator_path ]
      cmd += simulator_flags
      cmd.append(mainlua)
      self.window.run_command('exec', {'cmd': cmd, "file_regex": "(?i)^(?:ERROR: |WARNING: )[^C-Z]*([C-Z]:[^:]*):([0-9]+):([0-9]*)(.*)$" })
