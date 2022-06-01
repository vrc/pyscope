import pygame

class Scope (object):

    def __init__(self, xmax, ymax):
        self.size = (xmax, ymax)
        self.bg = pygame.Surface(self.size)
        self.setup_bg(self.bg)
        pygame.display.update()
        self.boundbox = pygame.Rect(0, 0, self.size[0], self.size[1])
        self.step = 1

    def setup_bg(self, bg):
        xline_count = 10
        yline_count = 8

        xmin = 5
        xmax = self.size[0] - 5
        xsize = xmax - xmin
        x0 = xmin + xsize // 2
        xline = xsize // xline_count
        xtick = xline // 5
        xline = xtick * 5
        xsize = xline * xline_count
        xmin = x0 - xsize // 2
        xmax = x0 + xsize // 2

        ymin = 20
        ymax = self.size[1]
        ysize = ymax - ymin
        y0 = ymin + ysize // 2
        yline = ysize // yline_count
        ytick = yline // 5
        yline = ytick * 5
        ysize = yline * yline_count
        ymin = y0 - ysize // 2
        ymax = y0 + ysize // 2

        self.xlim = (xmin, xmax)
        self.ylim = (ymin, ymax)
        self.x0 = x0
        self.y0 = y0

        bg.fill((0, 0, 0))        

        borderColor = (255, 255, 255)
        lineColor = (64, 64, 64)
        subDividerColor = (128, 128, 128)

        pygame.draw.rect(bg, borderColor, (xmin - 2, ymin - 2, xsize + 4, ysize + 4), 2)

        # draw the grid
        for i in range(1, yline_count):
            y = ymin + i * yline
            pygame.draw.line(bg, lineColor, (xmin, y), (xmax, y))
        for i in range(1, xline_count):
            x = xmin + i * xline
            pygame.draw.line(bg, lineColor, (x, ymin), (x, ymax))

        # draw the ticks
        tlen = 4
        for i in range(1, yline_count * 5):
            y = ymin + i * ytick
            pygame.draw.line(bg, subDividerColor, (x0 - tlen - 1, y), (x0 + tlen, y))
        for i in range(1, xline_count * 5):
            x = xmin + i * xtick
            pygame.draw.line(bg, subDividerColor, (x, y0 - tlen - 1), (x, y0 + tlen))

    def rect(self):
        return self.boundbox

    def set_step(self, step):
        self.step = step

    def draw(self, surface, samples):
        surface.blit(self.bg, self.rect())
        count = (self.xlim[1] - self.xlim[0] + self.step - 1) // self.step
        scale = (self.ylim[1] - self.ylim[0]) * 0.01
        p0 = [(self.xlim[0] + i * self.step, self.y0 - int(scale * v[0])) for i, v in enumerate(samples[-count:])]
        p1 = [(self.xlim[0] + i * self.step, self.y0 - int(scale * v[1])) for i, v in enumerate(samples[-count:])]
        p2 = [(self.xlim[0] + i * self.step, self.y0 - int(scale * v[2])) for i, v in enumerate(samples[-count:])]
        #p3 = [(self.xlim[0] + i, self.y0) for i, v in enumerate(samples)]
        pygame.draw.lines(surface, (200, 200, 0), False, p0)
        pygame.draw.lines(surface, (0, 200, 0), False, p1)
        pygame.draw.lines(surface, (0, 200, 200), False, p2)
        #pygame.draw.lines(surface, (0, 0, 200), False, p3)
        return self.rect()

