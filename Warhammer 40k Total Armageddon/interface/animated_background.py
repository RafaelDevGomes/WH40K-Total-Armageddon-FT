"""Fundo animado do menu principal."""
import math
import random

import pygame


CONFIG = {
    "duracao_ciclo": 6.0,
    "escala_max": 0.04,
    "deslocamento_y": 6.0,
    "deslocamento_x": 2.0,
    "brilho_olhos": 0.65,
    "brilho_planeta": 0.35,
    "qtd_particulas": 70,
    "velocidade_particulas": 28,
    "intensidade_vinheta": 0.55,
    "pausar_sem_foco": True,
}

# Posicoes dos pontos de luz na arte original (1365x768).
OLHO_ESQ = (612 / 1365, 232 / 768)
OLHO_DIR = (768 / 1365, 228 / 768)
PLANETA = (1135 / 1365, 195 / 768)


def _glow_surface(raio, cor):
    """Cria uma superficie de brilho radial pre-renderizada."""
    d = raio * 2
    pequena = pygame.Surface((32, 32), pygame.SRCALPHA)
    centro = 15.5
    for y in range(32):
        for x in range(32):
            distancia = math.hypot(x - centro, y - centro) / centro
            alfa = max(0.0, 1.0 - distancia) ** 2 * 255
            pequena.set_at((x, y), (*cor, int(alfa)))
    return pygame.transform.smoothscale(pequena, (d, d))


class AnimatedMenuBackground:
    """Fundo animado com ciclo senoidal, particulas e pausa por foco."""

    def __init__(self, caminho_imagem, tamanho, config=None):
        self.cfg = dict(CONFIG)
        if config:
            self.cfg.update(config)
        self.original = pygame.image.load(caminho_imagem).convert()
        self.t = 0.0
        self.pausado = False
        self._rng = random.Random(7)
        self.redimensionar(tamanho)

    def redimensionar(self, tamanho):
        self.tw, self.th = tamanho
        iw, ih = self.original.get_size()
        fator = max(self.tw / iw, self.th / ih) * (1.0 + self.cfg["escala_max"])
        self.cw = max(1, int(iw * fator))
        self.ch = max(1, int(ih * fator))
        self.base = pygame.transform.smoothscale(self.original, (self.cw, self.ch))
        self.ax = self.tw / 2
        self.ay = self.th
        self.bx = (self.tw - self.cw) / 2
        self.by = (self.th - self.ch) / 2
        self.glow_olho = _glow_surface(max(8, int(self.th * 0.09)), (255, 30, 20))
        self.glow_olho_nucleo = _glow_surface(max(5, int(self.th * 0.035)), (255, 82, 58))
        self.glow_planeta = _glow_surface(max(8, int(self.th * 0.16)), (255, 70, 25))
        self.vinheta = self._criar_vinheta()
        self._criar_particulas()

    def _criar_vinheta(self):
        pequena = pygame.Surface((64, 36), pygame.SRCALPHA)
        intensidade = self.cfg["intensidade_vinheta"]
        for y in range(36):
            for x in range(64):
                nx = (x - 31.5) / 31.5
                ny = (y - 17.5) / 17.5
                r2 = nx * nx + ny * ny
                alfa = min(1.0, max(0.0, (r2 - 0.35) / 1.1)) * intensidade
                pequena.set_at((x, y), (0, 0, 0, int(alfa * 255)))
        return pygame.transform.smoothscale(pequena, (self.tw, self.th))

    def _criar_particulas(self):
        self.particulas = []
        self._brasas = [_glow_surface(r, (255, 110, 35)) for r in (3, 4, 6)]
        for _ in range(self.cfg["qtd_particulas"]):
            self.particulas.append({
                "x": self._rng.uniform(0, self.tw),
                "y": self._rng.uniform(0, self.th),
                "v": self._rng.uniform(0.5, 1.4),
                "amp": self._rng.uniform(6, 28),
                "fase": self._rng.uniform(0, math.tau),
                "alpha": self._rng.uniform(0.35, 1.0),
                "tipo": self._rng.randrange(len(self._brasas)),
            })

    def tratar_evento(self, evento):
        """Trata redimensionamento e pausa quando a janela perde foco."""
        if evento.type == pygame.VIDEORESIZE:
            self.redimensionar((evento.w, evento.h))
        elif hasattr(pygame, "WINDOWSIZECHANGED") and evento.type == pygame.WINDOWSIZECHANGED:
            self.redimensionar((evento.x, evento.y))
        elif self.cfg["pausar_sem_foco"]:
            if hasattr(pygame, "WINDOWFOCUSLOST") and evento.type == pygame.WINDOWFOCUSLOST:
                self.pausado = True
            elif hasattr(pygame, "WINDOWFOCUSGAINED") and evento.type == pygame.WINDOWFOCUSGAINED:
                self.pausado = False

    def atualizar(self, dt):
        """Atualiza a animacao em segundos, independente do FPS."""
        if self.pausado:
            return
        dt = min(max(dt, 0.0), 0.1)
        self.t = (self.t + dt) % self.cfg["duracao_ciclo"]
        velocidade = self.cfg["velocidade_particulas"] * (self.th / 768.0)
        for particula in self.particulas:
            particula["y"] -= velocidade * particula["v"] * dt
            if particula["y"] < -10:
                particula["y"] = self.th + 10
                particula["x"] = self._rng.uniform(0, self.tw)

    def _fase(self):
        ciclo = self.cfg["duracao_ciclo"]
        return 0.5 - 0.5 * math.cos(math.tau * self.t / ciclo)

    def _transformar(self, x, y, escala, dx, dy):
        return (self.ax + (x - self.ax) * escala + dx,
                self.ay + (y - self.ay) * escala - dy)

    def desenhar(self, tela):
        cfg = self.cfg
        fase = self._fase()
        escala = 1.0 + cfg["escala_max"] * fase
        esc_tela = self.th / 768.0
        dy = cfg["deslocamento_y"] * esc_tela * fase
        dx = cfg["deslocamento_x"] * esc_tela * math.sin(math.tau * self.t / cfg["duracao_ciclo"])

        sw = int(self.cw * escala)
        sh = int(self.ch * escala)
        imagem = pygame.transform.smoothscale(self.base, (sw, sh))
        px, py = self._transformar(self.bx, self.by, escala, dx, dy)
        tela.blit(imagem, (int(px), int(py)))

        if cfg["brilho_olhos"] > 0:
            alfa = int(255 * cfg["brilho_olhos"] * (0.35 + 0.65 * fase))
            self.glow_olho.set_alpha(alfa)
            alfa_nucleo = int(255 * cfg["brilho_olhos"] * (0.22 + 0.58 * fase))
            self.glow_olho_nucleo.set_alpha(alfa_nucleo)
            gw, gh = self.glow_olho.get_size()
            nw, nh = self.glow_olho_nucleo.get_size()
            for fx, fy in (OLHO_ESQ, OLHO_DIR):
                ox, oy = self._transformar(self.bx + fx * self.cw, self.by + fy * self.ch,
                                           escala, dx, dy)
                tela.blit(self.glow_olho, (int(ox - gw / 2), int(oy - gh / 2)))
                tela.blit(self.glow_olho_nucleo,
                          (int(ox - nw / 2), int(oy - nh / 2)))

        if cfg["brilho_planeta"] > 0:
            pulso = 0.5 + 0.5 * math.sin(math.tau * self.t / cfg["duracao_ciclo"] + 1.2)
            self.glow_planeta.set_alpha(int(255 * cfg["brilho_planeta"] * (0.3 + 0.7 * pulso)))
            gw, gh = self.glow_planeta.get_size()
            ox, oy = self._transformar(self.bx + PLANETA[0] * self.cw,
                                       self.by + PLANETA[1] * self.ch, escala, dx, dy)
            tela.blit(self.glow_planeta, (int(ox - gw / 2), int(oy - gh / 2)))

        for particula in self.particulas:
            fade = math.sin(math.pi * max(0.0, min(1.0, particula["y"] / self.th))) ** 0.6
            pisca = 0.75 + 0.25 * math.sin(
                2 * math.tau * self.t / cfg["duracao_ciclo"] + particula["fase"])
            alfa = int(255 * particula["alpha"] * fade * pisca)
            if alfa <= 4:
                continue
            x = particula["x"] + particula["amp"] * math.sin(
                math.tau * self.t / cfg["duracao_ciclo"] + particula["fase"])
            brasa = self._brasas[particula["tipo"]]
            brasa.set_alpha(alfa)
            tela.blit(brasa, (int(x - brasa.get_width() / 2),
                              int(particula["y"] - brasa.get_height() / 2)))

        tela.blit(self.vinheta, (0, 0))
