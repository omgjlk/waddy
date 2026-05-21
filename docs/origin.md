# Origin

This is the unedited prompt @omgjlk gave to GitHub Copilot CLI on
2026-05-21 to bootstrap the waddy agent. It's preserved here verbatim so
anyone forking this repo can see what kicked it off — and so future-me
can remember what I was actually asking for.

---

> I'm going to have you build and be an agent named "waddy", a What Am I
> Doing Here agent. Your job is to track what it is I am spending my
> days doing. I primarily work in copilot-cli sessions, GitHub issues,
> GitHub Project Boards, GitHub Pull Requests, Slack discussions, Teams
> meetings, and Word documents. I also take notes in Apple Notes, but I
> will be migrating that to Obsidian. This agent will be backed by a
> personal repository. I plan to keep the repository open so that others
> may take inspiration from what I'm building, so we need to be very
> careful to not commit any sensitive matter to the repository. What I
> would like to do is be able to just dump words or links for whatever
> task I'm about to start and have you account for that via internal
> tracking plus a entry on my personal "WAIDH" project board. I want
> others to be able to glance at my board at any time and see the work
> I'm currently doing, work that's paused, and work I've finished. I
> wont always have an issue to begin with, we may need to make issues,
> or make entries on the project board directly without a backing issue
> or PR. Sometimes it'll just be that I'm reviewing a particularly large
> PR and we will want to account for that. Same for document reviews.
> Since I spend a lot of time on slack I will be asking you to review my
> slack output a few times a day to highlight where I'm spending that
> time. You might suggest creating some tracking issues based on that
> output, or just entries on the board for significant time spent or
> notable discussion outcomes. I also use the "saved for later" feature
> of slack to save things that I will need more time to process, so
> those will become "to do" like things. When I have meetings if there
> is a transcript available I'll want you to capture that and turn it
> into durable notes in my Obsidian setup (when it's ready).
>
> I'll want you to be able to see my work calendar and let me know of
> what is coming up in my day and what relevant info I should have, or
> what things I need to spend time on to prepare for the meetings. I
> may also want you to look at my personal calendar and call out
> conflicts. I will want you to be able to look at my running
> copilot-cli sessions to figure out what I am doing or what I have
> been doing, because I won't always remember to tell you ahead if time
> before I jump into a task. We will make use of the github-mcp-server
> for all things related to interacting with GitHub, and we'll use the
> slack plugin of that mcp for reading data out of slack. We will use
> the workiq mcp for dealing with my Outlook calendar / email / Teams /
> Office documents. We will develop skills as necessary.
>
> I will often ask you for a daily summary of what I did for that day,
> something I can share on slack. I will also ask you for a "what
> should I be doing today" report at the start of my day, which should
> consider my calendar, my ongoing projects, my incomplete work from
> the previous day, any new @ mentions or DMs in slack (assuming you
> can read them without them becoming marked as read).

---

## Notable follow-up that shaped the design

After the initial design was proposed, the user added a clarifying
constraint that ended up driving a significant rework of the task
lifecycle:

> So I have ADHD and I often multitask. When one agent session is
> working I'll use that time to move forward another agent session, or
> check on my slack messages or email. I'm definitely not going to be a
> 1 task at a time person.

This is why waddy models `active_tasks` as a set (not a current-task
pointer) and why `start-task` never auto-pauses anything. The soft
`switch-to` skill exists for the constant focus-changes; explicit
`pause-task` is reserved for actually setting work aside for hours or
days.
