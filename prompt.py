from textui.ansi import *
from textui.colors import *
from textui.getch import *
from fractions import Fraction

_PROMPT_OFFSET = 54

INTERACTIVE_MODE = 0
AUTOABORT_MODE = 1
AUTOCONFIRM_MODE = 2

class Prompt:
    def __init__(self):
        self._mode = None
        self.has_shown_menu = False
    def get_mode(self):
        return self._mode
    def set_mode(self, value):
        self._mode = value
    def can_interact(self):
        return (self._mode is None) or (self._mode == INTERACTIVE_MODE)

# Create a global instance to be used by the program.
prompter = Prompt()

# Write a question to stdout. Wait for the user to answer it.
# If defaultValue is set, show the value that will be used
# if the user just presses Enter.
def prompt(q, defaultValue = None, retry=False, normfunc=None, color=PARAM_COLOR, mask=None):
    while True:
        mode = prompter.get_mode()
        if mode is None:
            prompter.set_mode(INTERACTIVE_MODE)
        elif mode == AUTOCONFIRM_MODE:
            return defaultValue
        elif mode == AUTOABORT_MODE:
            print('mode = %s' % str(mode))
            raise Exception('Interactive prompting disallowed; aborting.')
        while q.startswith('\n'):
            print('')
            q = q[1:]
        txt = q
        width = len(txt)
        if not (defaultValue is None):
            defaultValue = str(defaultValue)
            txt = txt + " [" + color + str(defaultValue) + NORMTXT + "]"
            width += 3 + len(defaultValue)
        if width > _PROMPT_OFFSET:
            i = txt[0:_PROMPT_OFFSET].rindex(' ')
            print(txt[0:i])
            txt = INDENT + txt[i + 1:].lstrip()
            width = width - (i + 1) + len(INDENT)
        if width < _PROMPT_OFFSET:
            txt = txt + ' '*(_PROMPT_OFFSET-width)
        writec(txt + ": " + color)
        try:
            if mask:
                answer = readMasked()
            else:
                answer = sys.stdin.readline().strip()
            if not answer:
                answer = defaultValue
        finally:
            writec(NORMTXT)

        try:
            if normfunc:
                answer = normfunc(answer)
        except Exception as e:
            print(ERROR_COLOR+"Error: %s" % str(e)+NORMTXT)
            if retry:
                continue
            else:
                raise e
        finally:
            writec(NORMTXT)

        return answer
    return None

def readMasked():
    value = ''
    while True:
        c = getch()
        if (c == '\n') or (c == '\r') or (c == '\x1B'):
            print('')
            break
        elif (c == '\x08'):
            if len(value) > 0:
                value = value[:-1]
                sys.stdout.write('\b \b')
        else:
            value += c
            sys.stdout.write('*')
    return value

def _is_yes(answer):
    return bool(answer) and 'ty1'.find(answer.lower()[0]) != -1

def prompt_bool(q, defaultValue, retry=False):
    mode = prompter.get_mode()
    if mode == AUTOABORT_MODE:
        return False
    if mode == AUTOCONFIRM_MODE:
        return True
    return prompt(q, defaultValue, retry=retry, normfunc=_is_yes)

def _is_num(answer):
    if not answer or not answer.strip():
        raise Exception("Blank input is not a valid numeric value")
    try:
        num = float(answer)
    except ValueError:
        try:
            num = float(Fraction(answer))
        except ValueError:
            raise Exception("Cannot parse '%s' as a number" % answer)
    return num


def prompt_num(q, defaultValue=None, retry=False):
    return prompt(q, defaultValue, retry=retry, normfunc=_is_num)
