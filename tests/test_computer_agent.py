"""
Tests for the look → think → act → check loop in modules/screen_vision.py.

The desktop and the model are both faked: these check the loop's own judgement —
that it checks the screen after every action, drops a plan the screen contradicts,
refuses unverified "done" claims, never types into Devin's own terminal, and does not
let the model quit early — without touching a real screen or needing Ollama.
"""
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules import ollama_provider as llm  # noqa: E402
from modules import os_automation as oa  # noqa: E402
from modules import screen_vision as sv  # noqa: E402


CALC = {'window': 'Calculator', 'app': 'calc', 'elements': [
    {'role': 'push button', 'name': '7', 'x': 100, 'y': 300, 'w': 60, 'h': 60},
    {'role': 'push button', 'name': '=', 'x': 300, 'y': 500, 'w': 60, 'h': 60},
    {'role': 'push button', 'name': 'Clear', 'x': 400, 'y': 500, 'w': 60, 'h': 60},
]}
TERMINAL = {'window': 'kevin@host: ~', 'app': 'org.gnome.Terminal', 'elements': [
    {'role': 'push button', 'name': 'Close', 'x': 1240, 'y': 10, 'w': 30, 'h': 30},
    {'role': 'push button', 'name': 'Menu', 'x': 1200, 'y': 10, 'w': 30, 'h': 30},
]}
OVERVIEW = {'window': '', 'app': '', 'elements': [
    {'role': 'text', 'name': '', 'x': 400, 'y': 40, 'w': 400, 'h': 30, 'editable': True, 'focused': True,
     'shell': True},
    {'role': 'push button', 'name': 'Files', 'x': 500, 'y': 680, 'w': 40, 'h': 40, 'shell': True},
]}
BROWSER = {'window': 'New Tab - Web Browser', 'app': 'browser', 'elements': [
    {'role': 'entry', 'name': 'Address and search bar', 'x': 200, 'y': 60, 'w': 600, 'h': 30, 'focused': True},
    {'role': 'link', 'name': 'Images', 'x': 900, 'y': 120, 'w': 60, 'h': 20},
]}


class FakeDesktop:
    """Records what it was asked to do. `screens` maps an action to the screen it leads to."""

    def __init__(self, changes=True, screen=None, transitions=None):
        self.calls = []
        self.changes = changes
        self.screen = screen or CALC
        self.transitions = transitions or {}
        self.typed = ''

    def size(self):
        return (1280, 720)

    def capture(self):
        from PIL import Image
        return Image.new('RGB', (1280, 720), (30, 30, 30))

    def elements(self, budget=1.5, limit=160):
        out = dict(self.screen, elements=[dict(e) for e in self.screen['elements']])
        if self.typed:                      # typed text shows up in the field that has the keyboard
            for e in out['elements']:
                if e.get('focused'):
                    e['value'] = self.typed
        return out

    def settle(self, **kw):
        return {'stable': True, 'changed': self.changes, 'change': 0.2 if self.changes else 0.0, 'waited': 0.0}

    def mark(self):
        pass

    def _go(self, key):
        if key in self.transitions:
            self.screen = self.transitions[key]
            self.typed = ''

    def key(self, combo):
        self.calls.append(('key', combo))
        self._go(('key', combo))

    def type(self, text, interval=None):
        self.calls.append(('type', text))
        if any(e.get('focused') for e in self.screen['elements']):
            self.typed = text
        self._go(('type', text))

    def click(self, x, y, button='left', count=1):
        self.calls.append(('click', x, y, button, count))
        self._go(('click', x, y))

    def __getattr__(self, name):
        def record(*args, **kwargs):
            self.calls.append((name, *args))
        return record


class Script:
    """Stands in for the model: hands out replies (plans) and YES/NO verdicts in order."""

    def __init__(self, replies, verdicts=()):
        self.replies = list(replies)
        self.verdicts = list(verdicts)
        self.prompts = []
        self.systems = []

    def __call__(self, messages, system=None, **kw):
        self.prompts.append(messages[0]['content'])
        self.systems.append(system or '')
        raw = {'tokens_in': 10, 'tokens_out': 5, 'thinking': '', 'seconds': 0.0}
        if system == sv.VERIFY_SYSTEM:
            ok, reason = self.verdicts.pop(0) if self.verdicts else (True, 'the screen shows it.')
            return dict(raw, content=f'{reason}\nVERDICT: {"YES" if ok else "NO"}')
        return dict(raw, content=self.replies.pop(0) if self.replies else 'THINK: out of script\nfail "out of script"')

    @property
    def plans(self):
        return [p for p, s in zip(self.prompts, self.systems) if s != sv.VERIFY_SYSTEM]


class LoopTestCase(unittest.TestCase):
    task = 'compute 7 on the calculator'

    def run_agent(self, replies, verdicts=(), changes=True, max_steps=20, screen=None, transitions=None,
                  env=None):
        self.desk = FakeDesktop(changes, screen, transitions)
        self.script = Script(replies, verdicts)
        self.events = []
        with patch.object(llm, 'chat_text', self.script), \
             patch.object(llm, 'pick_agent_model', return_value='fake'), \
             patch.object(llm, 'supports_vision', return_value=False), \
             patch.object(sv, 'ocr_available', return_value=False), \
             patch.dict(os.environ, env or {}), \
             patch.object(oa, '_tmp_path', lambda name: os.path.join('/tmp', 'devin_test_' + name)):
            agent = sv.ComputerAgent(desktop=self.desk, on_event=self.events.append, max_steps=max_steps)
            return agent.run(self.task)

    def kinds(self):
        return [c[0] for c in self.desk.calls]


class TestLoop(LoopTestCase):
    def test_acts_then_finishes_when_the_screen_confirms(self):
        r = self.run_agent(['THINK: press 7.\nclick "7"\ndone "The calculator shows 7."'],
                           verdicts=[(True, 'display shows 7')])
        self.assertTrue(r.success)
        self.assertEqual(r.answer, 'The calculator shows 7.')
        self.assertIn(('click', 130, 330, 'left', 1), self.desk.calls)
        self.assertEqual(r.thinks, 1)        # one plan was enough: nothing went wrong

    def test_a_whole_plan_runs_without_asking_the_model_again(self):
        r = self.run_agent(['THINK: three presses.\nclick "7"\nclick "="\nclick "Clear"\ndone "ok"'])
        self.assertTrue(r.success)
        self.assertEqual(self.kinds().count('click'), 3)
        self.assertEqual(len(self.script.plans), 1)

    def test_a_plan_that_forgets_to_say_done_is_checked_against_the_screen(self):
        r = self.run_agent(['THINK: press 7.\nclick "7"'], verdicts=[(True, 'The display shows 7.')])
        self.assertTrue(r.success)
        self.assertEqual(r.answer, 'The display shows 7.')
        self.assertEqual(len(self.script.plans), 1)      # it did not go on fiddling after reaching the goal

    def test_an_unfinished_plan_is_continued_with_the_reason(self):
        r = self.run_agent(['THINK: press 7.\nclick "7"', 'THINK: and equals.\nclick "="\ndone "It shows 7."'],
                           verdicts=[(False, 'equals was not pressed'), (True, 'ok')])
        self.assertTrue(r.success)
        self.assertTrue(any('equals was not pressed' in p for p in self.script.plans))

    def test_false_done_is_rejected_and_work_continues(self):
        r = self.run_agent(['THINK: all good\ndone "Done!"',
                            'THINK: press 7\nclick "7"\ndone "It shows 7."'],
                           verdicts=[(False, 'nothing was pressed yet'), (True, 'display shows 7')])
        self.assertTrue(r.success)
        self.assertEqual(r.answer, 'It shows 7.')
        self.assertTrue(any(s.action == 'done' and 'REJECTED' in s.outcome for s in r.steps))
        # the model was told why its claim was refused
        self.assertTrue(any('nothing was pressed yet' in p for p in self.script.plans))

    def test_repeated_false_done_ends_as_failure_not_success(self):
        r = self.run_agent(['THINK: x\ndone "Done!"'] * 6, verdicts=[(False, 'still the same screen')] * 6)
        self.assertFalse(r.success)
        self.assertIn('could not get the screen to show', r.answer)
        self.assertIn('still the same screen', r.answer)
        self.assertEqual(self.desk.calls, [])        # it did not start changing things at random

    def test_an_action_without_effect_stops_the_plan_and_replans(self):
        r = self.run_agent(['THINK: click it\nclick "="\nclick "7"\ndone "ok"',
                            'THINK: click again\nclick "="',
                            'THINK: keys then\nkey enter\ndone "done"'],
                           changes=False)
        # the click after the failed one was NOT carried out blindly
        self.assertEqual(self.kinds().count('click'), 2)
        self.assertTrue(any(e['type'] == 'retry' for e in self.events))
        self.assertTrue(any('changed nothing' in p for p in self.script.plans))
        self.assertTrue(any('not getting anywhere' in p for p in self.script.plans))
        self.assertIn(('key', 'enter'), self.desk.calls)

    def test_an_element_that_does_nothing_is_not_offered_again(self):
        self.run_agent(['THINK: a\nclick "="', 'THINK: b\nfail "x"', 'fail "x"', 'fail "x"'], changes=False)
        self.assertIn('button "="', self.script.plans[0])
        self.assertNotIn('button "="', self.script.plans[1])

    def test_giving_up_early_is_not_accepted(self):
        r = self.run_agent(['THINK: hard\nfail "cannot"', 'THINK: press 7\nclick "7"\ndone "It shows 7."'])
        self.assertTrue(r.success)
        self.assertTrue(any('Do not give up yet' in p for p in self.script.plans))

    def test_unknown_label_is_reported_not_clicked(self):
        with patch.object(sv.threading.Event, 'wait', lambda self, t=None: False):
            r = self.run_agent(['THINK: x\nclick "Submit order"\ndone "ok"', 'THINK: y\nclick "7"\ndone "ok"'])
        self.assertEqual(self.kinds().count('click'), 1)
        self.assertIn('nothing on the screen is labelled "Submit order"', r.steps[0].outcome)
        self.assertTrue(r.success)

    def test_unknown_element_id_is_reported_not_clicked(self):
        r = self.run_agent(['THINK: x\nclick 99', 'THINK: ok\nclick "7"\ndone "done"'])
        self.assertEqual(self.kinds().count('click'), 1)
        self.assertIn('no element with id 99', r.steps[0].outcome)

    def test_runs_out_of_steps_honestly(self):
        r = self.run_agent(['THINK: w\nwait 0.2\nkey tab\nkey escape\nkey tab\ndone "x"'], max_steps=3)
        self.assertFalse(r.success)
        self.assertIn('still not finished', r.answer)

    def test_a_model_that_writes_no_actions_ends_as_failure(self):
        r = self.run_agent(['I am not sure what to do here.'] * 4)
        self.assertFalse(r.success)
        self.assertIn('did not give me any action', r.answer)
        self.assertEqual(self.desk.calls, [])


class TestTypingGoesToTheRightPlace(LoopTestCase):
    task = 'search the web for valleys'

    def test_never_types_into_the_terminal_devin_runs_in(self):
        r = self.run_agent(['THINK: type it\ntype "valleys" ENTER\ndone "searched"', 'fail "x"', 'fail "x"', 'fail "x"'],
                           screen=TERMINAL)
        self.assertNotIn('type', self.kinds())
        self.assertIn('BLOCKED', r.steps[0].outcome)
        self.assertTrue(any('terminal that runs Devin' in p for p in self.script.plans))

    def test_never_closes_the_terminal_devin_runs_in(self):
        self.run_agent(['THINK: a\nkey alt+f4', 'THINK: b\nclick "Close"', 'THINK: c\nkey ctrl+c', 'fail "x"',
                        'fail "x"', 'fail "x"'], screen=TERMINAL)
        self.assertEqual(self.desk.calls, [])
        self.assertNotIn('"Close"', self.script.plans[0])       # the button is not even offered

    def test_opens_the_app_first_then_types_there(self):
        r = self.run_agent(
            ['THINK: open the browser, then search.\nkey super\ntype "browser" ENTER\n'
             'type "valleys" ENTER\ndone "results are showing"',
             'THINK: the browser is open with the keyboard in its address bar.\n'
             'type "valleys" ENTER\ndone "results are showing"'],
            screen=TERMINAL,
            transitions={('key', 'super'): OVERVIEW, ('key', 'enter'): BROWSER})
        self.assertTrue(r.success)
        self.assertEqual([c for c in self.desk.calls if c[0] in ('key', 'type')],
                         [('key', 'super'), ('type', 'browser'), ('key', 'enter'),
                          ('type', 'valleys'), ('key', 'enter')])
        self.assertIn('now in front: "New Tab - Web Browser"', r.steps[1].outcome)

    def test_a_new_window_is_read_before_the_plan_goes_on(self):
        chooser = {'window': 'Who is using this?', 'app': 'browser', 'elements': [
            {'role': 'push button', 'name': 'Guest', 'x': 300, 'y': 300, 'w': 100, 'h': 40}]}
        r = self.run_agent(
            ['THINK: open and search.\nkey super\ntype "browser" ENTER\ntype "valleys" ENTER\ndone "results"',
             'THINK: it asks who is using it; pick one first.\nclick "Guest"\ntype "valleys" ENTER\ndone "results"'],
            screen=TERMINAL,
            transitions={('key', 'super'): OVERVIEW, ('key', 'enter'): chooser, ('click', 350, 320): BROWSER})
        # the search words were NOT typed blindly into the unexpected chooser: the chooser came first
        order = [c[:2] for c in self.desk.calls if c[0] in ('type', 'click')]
        self.assertEqual(order, [('type', 'browser'), ('click', 350), ('type', 'valleys')])
        self.assertTrue(r.success)
        self.assertIn('A new window is in front now: "Who is using this?"', self.script.plans[1])
        self.assertIn('"Guest"', self.script.plans[1])
        self.assertIn(('click', 350, 320, 'left', 1), self.desk.calls)

    def test_apps_are_opened_with_the_mouse_from_the_launcher_on_screen(self):
        top_bar = {'role': 'push button', 'name': 'Activities', 'x': 10, 'y': 4, 'w': 60, 'h': 20, 'shell': True}
        terminal = dict(TERMINAL, elements=TERMINAL['elements'] + [top_bar])
        results = dict(OVERVIEW, elements=OVERVIEW['elements'] + [
            {'role': 'push button', 'name': 'Web Browser', 'x': 600, 'y': 300, 'w': 80, 'h': 80, 'shell': True}])
        r = self.run_agent(
            ['THINK: open it from the launcher.\nclick "Activities"\ntype "browser"\nclick "Web Browser"\n'
             'click "Address and search bar"\ntype "valleys" ENTER\ndone "results are showing"',
             'THINK: the browser is open.\nclick "Address and search bar"\ntype "valleys" ENTER\n'
             'done "results are showing"'],
            screen=terminal,
            transitions={('click', 40, 14): results, ('click', 640, 340): BROWSER})
        self.assertTrue(r.success, [s.outcome for s in r.steps])
        self.assertIn('click "Activities"', self.script.systems[0])      # the rule names what is on this screen
        self.assertIn('Devin itself runs in', self.script.plans[0])
        self.assertEqual([c[0] for c in self.desk.calls], ['click', 'type', 'click', 'click', 'type', 'key'])
        self.assertEqual(len(self.script.plans), 2)                      # one per window, not one per click

    def test_text_inside_devins_own_terminal_is_never_a_click_target(self):
        chatter = {'role': 'label', 'name': 'Web Browser opened, so the task was done', 'x': 100, 'y': 300, 'w': 400, 'h': 20}
        terminal = dict(TERMINAL, elements=TERMINAL['elements'] + [chatter])
        with patch.object(sv.threading.Event, 'wait', lambda self, t=None: False):
            r = self.run_agent(['THINK: there it is\nclick "Web Browser"\ndone "ok"', 'fail "x"', 'fail "x"', 'fail "x"'],
                               screen=terminal)
        self.assertNotIn('click', self.kinds())
        self.assertNotIn('Web Browser opened', self.script.plans[0])
        self.assertIn('nothing on the screen is labelled', r.steps[0].outcome)

    def test_nothing_is_typed_when_no_text_field_has_the_keyboard(self):
        # letters sent to a window without a focused field can be commands in that program
        r = self.run_agent(['THINK: a\ntype "hello"\nclick "7"\ndone "ok"', 'fail "x"', 'fail "x"', 'fail "x"'])
        self.assertNotIn('type', self.kinds())
        self.assertIn('no text field has the keyboard', r.steps[0].outcome)
        self.assertNotIn('click', self.kinds())      # the rest of the plan was dropped

    def test_clicking_a_field_first_makes_typing_allowed(self):
        r = self.run_agent(['THINK: a\nclick "7"\ntype "hello"\ndone "ok"', 'fail "x"', 'fail "x"', 'fail "x"'])
        self.assertEqual(self.kinds()[:2], ['click', 'type'])

    def test_text_the_field_already_holds_is_not_typed_twice(self):
        held = dict(OVERVIEW, elements=[dict(OVERVIEW['elements'][0], value='burpsuite')] + OVERVIEW['elements'][1:])
        r = self.run_agent(['THINK: a\ntype "burpsuite"\nclick "Files"\ndone "ok"'], screen=held)
        self.assertNotIn('type', self.kinds())
        self.assertIn('already reads "burpsuite"', r.steps[0].outcome)
        self.assertIn('click', self.kinds())                 # and the plan simply goes on

    def test_single_letters_pressed_as_keys_need_a_text_field_too(self):
        r = self.run_agent(['THINK: a\nkey f\nkey 2\ndone "ok"', 'fail "x"', 'fail "x"', 'fail "x"'])
        self.assertEqual(self.desk.calls, [])
        self.assertIn('no text field has the keyboard', r.steps[0].outcome)

    def test_typing_that_lands_nowhere_is_noticed(self):
        # clicked first, typed, but the text shows up nowhere and the screen does not change
        r = self.run_agent(['THINK: a\nclick "7"\ntype "hello"\nclick "="\ndone "ok"', 'fail "x"', 'fail "x"', 'fail "x"'],
                           changes=False)
        self.assertIn('changed nothing', r.steps[0].outcome)
        self.assertEqual(self.kinds().count('click'), 1)      # the rest of the plan was dropped

    def test_notifications_and_the_top_bar_are_not_click_targets(self):
        banner = {'role': 'text', 'name': '', 'value': 'Web Browser', 'x': 500, 'y': 50, 'w': 120, 'h': 16, 'shell': True}
        clock = {'role': 'menu', 'name': 'System', 'x': 1250, 'y': 4, 'w': 60, 'h': 20, 'shell': True}
        screen = dict(CALC, elements=CALC['elements'] + [banner, clock])
        with patch.object(sv.threading.Event, 'wait', lambda self, t=None: False):
            r = self.run_agent(['THINK: a\nclick "Web Browser"', 'THINK: b\nclick "System"', 'fail "x"', 'fail "x"', 'fail "x"'],
                               screen=screen)
        self.assertNotIn('click', self.kinds())
        self.assertNotIn('Web Browser', self.script.plans[0].split('ON SCREEN')[1])

    def test_typed_text_is_confirmed_from_the_field(self):
        r = self.run_agent(['THINK: a\ntype "valleys"\ndone "typed"'], screen=BROWSER)
        self.assertIn('the field now reads "valleys"', r.steps[0].outcome)


SYSTEM_MENU = {'window': 'New Tab - Web Browser', 'app': 'browser', 'elements': BROWSER['elements'] + [
    {'role': 'menu', 'name': 'System', 'x': 1250, 'y': 4, 'w': 60, 'h': 20, 'shell': True},
    {'role': 'push button', 'name': 'Restart…', 'x': 1100, 'y': 200, 'w': 120, 'h': 30, 'shell': True},
    {'role': 'push button', 'name': 'Power Off…', 'x': 1100, 'y': 240, 'w': 120, 'h': 30, 'shell': True},
    {'role': 'push button', 'name': 'Log Out…', 'x': 1100, 'y': 280, 'w': 120, 'h': 30, 'shell': True},
]}
COUNTDOWN = {'window': 'New Tab - Web Browser', 'app': 'browser', 'elements': BROWSER['elements'] + [
    {'role': 'text', 'name': '', 'value': 'The system will restart automatically in 60 seconds.',
     'x': 500, 'y': 300, 'w': 400, 'h': 20, 'shell': True},
    {'role': 'push button', 'name': 'Cancel', 'x': 500, 'y': 360, 'w': 100, 'h': 30, 'shell': True},
    {'role': 'push button', 'name': 'Restart', 'x': 700, 'y': 360, 'w': 100, 'h': 30, 'shell': True},
]}


class TestNeverEndsTheSession(LoopTestCase):
    """A real run once restarted the user's computer. None of these may ever reach the desktop."""
    task = 'search the web for valleys'

    def test_restart_power_off_and_log_out_are_never_clicked(self):
        r = self.run_agent(['THINK: a\nclick "Restart"', 'THINK: b\nclick "Power Off"', 'THINK: c\nclick "Log Out"',
                            'THINK: d\nclick 5', 'fail "x"', 'fail "x"', 'fail "x"'], screen=SYSTEM_MENU)
        self.assertNotIn('click', self.kinds())
        self.assertTrue(all('BLOCKED' in s.outcome for s in r.steps[:3]))

    def test_they_and_the_system_menus_are_not_even_offered(self):
        self.run_agent(['fail "x"', 'fail "x"', 'fail "x"'], screen=SYSTEM_MENU)
        for name in ('Restart', 'Power Off', 'Log Out', '"System"'):
            self.assertNotIn(name, self.script.plans[0])
        self.assertIn('Images', self.script.plans[0])

    def test_session_ending_keys_and_commands_are_refused(self):
        r = self.run_agent(['THINK: a\nkey ctrl+alt+delete', 'THINK: b\ntype "sudo reboot" ENTER',
                            'THINK: c\ntype "systemctl poweroff" ENTER', 'THINK: d\ntype "rm -rf ~" ENTER',
                            'fail "x"', 'fail "x"', 'fail "x"'], screen=BROWSER)
        self.assertEqual(self.desk.calls, [])
        self.assertTrue(all('BLOCKED' in s.outcome for s in r.steps[:4]))

    def test_a_restart_countdown_is_cancelled_at_once(self):
        r = self.run_agent(['THINK: a\nclick "Images"\ntype "valleys" ENTER\ndone "ok"', 'fail "x"', 'fail "x"', 'fail "x"'],
                           screen=BROWSER, transitions={('click', 930, 130): COUNTDOWN})
        self.assertIn(('key', 'escape'), self.desk.calls)
        self.assertIn('it was cancelled', r.steps[0].outcome)
        self.assertNotIn('type', self.kinds())               # the rest of the plan was dropped
        self.assertNotIn(('click', 750, 375, 'left', 1), self.desk.calls)

    def test_only_a_task_that_asks_for_it_may_restart(self):
        self.task = 'restart the computer'
        self.run_agent(['THINK: asked for.\nclick "Restart"', 'fail "x"', 'fail "x"', 'fail "x"'], screen=SYSTEM_MENU)
        self.assertIn(('click', 1160, 215, 'left', 1), self.desk.calls)


class TestParsing(unittest.TestCase):
    def test_plan_lines(self):
        thought, acts = sv.parse_reply(
            'THINK: open it first.\nkey super\ntype "chrome" ENTER\nclick "Images"\nscroll down 3\n'
            'done "pictures are showing"\nthis line is never reached')
        self.assertEqual(thought, 'open it first.')
        self.assertEqual([a['action'] for a in acts], ['key', 'type', 'click', 'scroll', 'done'])
        self.assertEqual(acts[1], {'action': 'type', 'text': 'chrome', 'enter': True})
        self.assertEqual(acts[2]['target'], 'Images')
        self.assertEqual(acts[4]['answer'], 'pictures are showing')

    def test_sloppy_but_clear_lines_are_understood(self):
        _, acts = sv.parse_reply('1. Press the Super key\n2. type "a b" and press Enter\n- key Ctrl + L\n'
                                 'double-click "notes.txt"\nclick 640, 360\npress enter to search')
        self.assertEqual(acts[0]['keys'], 'super')
        self.assertTrue(acts[1]['enter'])
        self.assertEqual(acts[2]['keys'], 'ctrl+l')
        self.assertEqual(acts[3]['button'], 'double')
        self.assertEqual((acts[4]['x'], acts[4]['y']), (640, 360))
        self.assertEqual(acts[5]['keys'], 'enter')

    def test_a_line_that_is_just_a_key_name_is_a_key_press(self):
        _, acts = sv.parse_reply('click "Activities"\ntype "calculator"\nenter\nescape\nctrl+l')
        self.assertEqual(acts[1], {'action': 'type', 'text': 'calculator', 'enter': True})
        self.assertEqual([a.get('keys') for a in acts[2:]], ['escape', 'ctrl+l'])

    def test_prose_is_not_mistaken_for_actions(self):
        thought, acts = sv.parse_reply('I think we should look at the screen more carefully before acting.')
        self.assertEqual(acts, [])
        self.assertTrue(thought)
        self.assertIsNone(sv.parse_action('type the name of the application you want and then hit the key.'))
        self.assertIsNone(sv.parse_action('key banana'))

    def test_labels_are_matched_the_way_a_person_means_them(self):
        els = [sv.Element(1, 'link', 'Images', 0, 0, 10, 10), sv.Element(2, 'label', 'lmages of valleys', 0, 50, 10, 10, source='ocr'),
               sv.Element(3, 'push button', 'Sign in', 0, 90, 10, 10), sv.Element(4, 'entry', 'Address and search bar', 0, 120, 10, 10)]
        self.assertEqual(sv.match_element(els, 'Images').id, 1)
        self.assertEqual(sv.match_element(els, 'the Images tab').id, 1)
        self.assertEqual(sv.match_element(els, 'sign in button').id, 3)
        self.assertEqual(sv.match_element(els, 'address bar').id, 4)
        self.assertIsNone(sv.match_element(els, 'Downloads'))

    def test_a_name_is_found_whether_or_not_it_is_written_with_spaces(self):
        els = [sv.Element(1, 'label', 'burpsuite', 0, 200, 80, 20, shell=True),
               sv.Element(2, 'push button', 'Terminal', 0, 700, 40, 40, shell=True)]
        self.assertEqual(sv.match_element(els, 'Burp Suite Community').id, 1)
        self.assertEqual(sv.match_element(els, 'Burp Suite').id, 1)

    def test_a_search_box_is_not_mistaken_for_the_thing_typed_into_it(self):
        els = [sv.Element(1, 'entry', '', 0, 0, 300, 30, value='calculator', focused=True),
               sv.Element(2, 'label', 'Calculator', 0, 200, 80, 20),
               sv.Element(3, 'label', 'MATE Calculator', 200, 200, 80, 20, source='ocr')]
        self.assertEqual(sv.match_element(els, 'Calculator').id, 2)
        self.assertEqual(sv.match_element(els, 'MATE Calculator').id, 3)


class TestPureMouseAndKeyboard(unittest.TestCase):
    def test_shell_is_off_unless_enabled(self):
        with patch.dict(os.environ, {'DEVIN_ALLOW_SHELL': '0'}):
            self.assertNotIn('shell', sv.action_names())
            self.assertIsNone(sv.parse_action('shell ls -la'))
            self.assertIn('open the Terminal application', sv.system_prompt(False))
        with patch.dict(os.environ, {'DEVIN_ALLOW_SHELL': '1'}):
            self.assertIn('shell', sv.action_names())
            self.assertEqual(sv.parse_action('shell ls -la')['command'], 'ls -la')

    def test_dangerous_commands_are_recognised(self):
        for cmd in ('rm -rf /', 'rm -rf ~', 'sudo mkfs.ext4 /dev/sda1', 'dd if=/dev/zero of=/dev/sda', 'reboot'):
            self.assertTrue(sv._DANGEROUS.search(cmd), cmd)
        for cmd in ('ls -la', 'rm notes.txt', 'df -h', 'pip install requests'):
            self.assertFalse(sv._DANGEROUS.search(cmd), cmd)


class TestModelChoice(unittest.TestCase):
    def test_a_seeing_model_operates_the_computer_even_when_a_blind_one_is_pinned(self):
        caps = {'tiny:0.5b': {'capabilities': ['completion'], 'params_b': 0.5},
                'eyes:4b': {'capabilities': ['completion', 'vision'], 'params_b': 4.0}}
        with patch.object(llm, 'list_models', return_value=list(caps)), \
             patch.object(llm, 'model_info', lambda m: caps[m]), \
             patch.dict(os.environ, {'OLLAMA_MODEL': 'tiny:0.5b', 'DEVIN_AGENT_MODEL': ''}):
            self.assertEqual(llm.pick_model(), 'tiny:0.5b')
            self.assertEqual(llm.pick_agent_model(), 'eyes:4b')


if __name__ == '__main__':
    unittest.main()
