import pygame

def btn_pos(offs, row, col, size):
    x = 15 + col * (size[0] + 12)
    y = offs + 5 + row * (size[1] + 5)
    return (x, y)

class Text (object):
    font = None

    def __init__(self, label):
        if self.font is None:
            # can only do this once pygame.font.init() has been called
            self.__class__.font = pygame.font.SysFont('notomono', 20)
        self.color = (0, 0, 0)
        self.label = label

    def _redraw(self):
        self.text = self.font.render(self.label, True, self.color)

    def set_color(self, color):
        self.color = color
        self._redraw()

    def set_text(self, label):
        self.label = label
        self._redraw()

class Label (Text):

    def __init__(self, label, pos, size=None):
        super().__init__(label)
        self.ena = True
        self.size = size
        self.set_text(label)
        self.rect = pygame.Rect(pos, self.size)

    def _redraw(self):
        text = self.font.render(self.label, True, self.color if self.ena else (100, 100, 100))

        if self.size is None:
            self.size = text.get_size()

        self.lbl = pygame.Surface(self.size)

        self.lbl.fill((200, 200, 200))
        dx = max(0, (self.lbl.get_width() - text.get_width()) // 2)
        dy = max(0, (self.lbl.get_height() - text.get_height()) // 2)
        self.lbl.blit(text, (dx, dy))

    def draw(self, surface):
        return surface.blit(self.lbl, self.rect)

    def press(self, pos):
        pass

    def depress(self, pos):
        pass

    def enable(self, ena=True):
        if self.ena != ena:
            self.ena = ena
            self._redraw()

class PushButton (Text):

    StateEnabled = 0
    StateArmed = 1
    StateDisabled = 2

    def __init__(self, label, on_click, pos, size=None):
        super().__init__(label)

        self.on_click = on_click
        self.state = self.StateEnabled
        self.size = size
        self._redraw()
        self.rect = pygame.Rect(pos, self.size)

    def _redraw(self):
        color= [(0, 0, 0), (255, 255, 255), (100, 100, 100)][self.state]
        text = self.font.render(self.label, True, color)

        if self.size is None:
            self.size = text.get_size()
            self.size = (self.size[0] + 4, self.size[1] + 4)
        size = self.size

        self.btn = pygame.Surface(size)
        self.btn.fill((200, 200, 200))

        dx = (self.btn.get_width() - text.get_width()) // 2
        dy = (self.btn.get_height() - text.get_height()) // 2

        if self.state != self.StateDisabled:
            ghost = self.font.render(self.label, True, (255 - color[0], 255 - color[1], 255 - color[2]))
            self.btn.blit(ghost, (dx+1, dy+1))
            self.btn.blit(text, (dx-1, dy-1))
        else:
            self.btn.blit(text, (dx, dy))

        if self.state == self.StateEnabled:
            pygame.draw.lines(self.btn, (50, 50, 50), False, [(size[0]-1, 1), (size[0]-1, size[1]-1), (1, size[1] - 1)], 3)
            pygame.draw.lines(self.btn, (255, 255, 255), False, [(size[0]-1, 1), (1, 1), (1, size[1] - 1)], 3)

        if self.state == self.StateArmed:
            pygame.draw.lines(self.btn, (50, 50, 50), False, [(size[0]-1, 1), (1, 1), (1, size[1] - 1)], 3)
            pygame.draw.lines(self.btn, (255, 255, 255), False, [(size[0]-1, 1), (size[0]-1, size[1]-1), (1, size[1] - 1)], 3)

    def draw(self, surface):
        return surface.blit(self.btn, self.rect)

    def press(self, pos):
        if self.state == self.StateEnabled and self.rect.collidepoint(pos):
            self.state = self.StateArmed
            self._redraw()

    def depress(self, pos):
        if self.state == self.StateArmed:
            self.state = self.StateEnabled
            self._redraw()
            if self.on_click and self.rect.collidepoint(pos):
                self.on_click(self)

    def enable(self, ena=True):
        self.state = self.StateEnabled if ena else self.StateDisabled
        self._redraw()

class Setting (object):

    def __init__(self, label, on_update, current, settings, pos, btn_offs, btn_size):
        self.btns = []
        self.btns.append(PushButton(f"{label} +", lambda b: self.setting_next(), btn_pos(btn_offs, pos[0]+0, pos[1], btn_size), btn_size))
        self.btns.append(PushButton(f"{label} -", lambda b: self.setting_prev(), btn_pos(btn_offs, pos[0]+2, pos[1], btn_size), btn_size))
        self.lbl = Label(current, btn_pos(btn_offs, pos[0]+1, pos[1], btn_size), btn_size)
        self.settings = settings
        self.index = self.settings.index(current)
        self.idx = self.index
        self.on_update = on_update
        self.update(False)

    def update(self, notify=True):
        self.btns[0].enable(self.index < (len(self.settings) - 1))
        self.btns[1].enable(self.index > 0)
        self.lbl.set_text(self.settings[self.index])
        if notify and self.on_update:
            self.on_update(self)

    def setting_next(self):
        self.index = min(self.index + 1, len(self.settings) - 1)
        self.update()

    def setting_prev(self):
        self.index = max(self.index - 1, 0)
        self.update()

    def setting_reset(self):
        self.index = self.idx
        self.update()

    def draw(self, surface):
        for btn in self.btns:
            btn.draw(surface)
        self.lbl.draw(surface)
        return self.rect()

    def press(self, pos):
        for btn in self.btns:
            btn.press(pos)

    def depress(self, pos):
        for btn in self.btns:
            btn.depress(pos)

    def enable(self, ena=True):
        for btn in self.btns:
            btn.enable(ena)
        self.lbl.enable(ena)

    def rect(self):
        return self.btns[0].rect.union(self.btns[1].rect)
