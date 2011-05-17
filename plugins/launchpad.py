#   Copyright 2011 Paul Voccio
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""Pyhole Launchpad Plugin"""

from launchpadlib.launchpad import Launchpad as LP

from pyhole import plugin
from pyhole import utils


class Launchpad(plugin.Plugin):
    """Provide access to the Launchpad API"""

    def __init__(self, irc, conf):
        self.irc = irc
        self.launchpad = LP.login_anonymously("pyhole", "production",
                self.irc.cache)

    @plugin.hook_add_command("lbugs")
    @utils.spawn
    def lbugs(self, params=None, **kwargs):
        """Launchpad bugs for a team (ex: .lbugs <project> <team>|<user>)"""
        if params:
            project, team = params.split(" ", 2)
            try:
                members = self.launchpad.people[team]
                proj = self.launchpad.projects[project]

                if len(members.members) < 2:
                    # Find a single member
                    self._find_bugs(members, proj)
                else:
                    # Find everyone on the team
                    for i, person in enumerate(members.members):
                        if i <= 4:
                            self.irc.log.debug("LP: %s" % person.display_name)
                            self._find_bugs(person, proj, False)
                        else:
                            self.irc.reply("[...] truncated last %d users" % (
                                    len(members.members) - i))
                            break
            except KeyError:
                self.irc.reply("Unable to find user '%s' in Launchpad" % team)
        else:
            self.irc.reply(self.lbugs.__doc__)

    @plugin.hook_add_keyword("lp")
    @utils.spawn
    def keyword_lp(self, params=None, **kwargs):
        """Retrieve Launchpad bug information (ex: LP12345)"""
        if params:
            params = utils.ensure_int(params)

            if not params:
                return

            try:
                bug = self.launchpad.bugs[params]
                task = bug.bug_tasks[len(bug.bug_tasks) - 1]

                self.irc.reply("LP %s [Status: %s, Assignee: %s] %s" % (
                        task.title, task.status,
                        self._find_name(task.assignee_link), bug.web_link))
            except Exception:
                return

    def _find_name(self, user):
        """Lookup a Launchpad user's display name"""
        try:
            return self.launchpad.people[user].display_name
        except ValueError:
            return "None"

    def _find_bugs(self, person, project, single=True):
        """Lookup Launchpad bugs"""
        bugs = project.searchTasks(assignee=person)
        for i, bug in enumerate(bugs):
            if i <= 4:
                self.irc.reply("LP %s [Assignee: %s] %s" % (bug.title,
                        person.display_name, bug.web_link))
            else:
                self.irc.reply("[...] truncated last %d bugs" % (
                        len(bugs) - i))
                break

        if single and i < 1:
            self.irc.reply("No bugs found for %s" % (person.display_name))
