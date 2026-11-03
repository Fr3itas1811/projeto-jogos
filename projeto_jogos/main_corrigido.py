import pygame
import sys
import math
import random

pygame.init()
random.seed(7)

# =====================================================================
#  CONFIGURAÇÕES DA TELA
# =====================================================================
LARGURA = 640
ALTURA = 400
ESCALA = 2
E = ESCALA

tela = pygame.display.set_mode((LARGURA * E, ALTURA * E))
pygame.display.set_caption("Football Career")

jogo = pygame.Surface((LARGURA, ALTURA))                      # mundo (pixel art)
grande = pygame.Surface((LARGURA * E, ALTURA * E))            # mundo ampliado
ui = pygame.Surface((LARGURA * E, ALTURA * E), pygame.SRCALPHA)  # interface nítida
camada_sombra = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)

relogio = pygame.time.Clock()

# =====================================================================
#  CORES
# =====================================================================
BRANCO = (255, 255, 255)
PRETO = (20, 20, 25)
LINHA = (236, 242, 236)
AMARELO = (255, 210, 40)
AZUL_UI = (30, 100, 220)
VERMELHO_UI = (210, 40, 45)
CONTORNO = (14, 14, 24)

# =====================================================================
#  ESTADOS DO JOGO
# =====================================================================
MENU = "menu"
JOGANDO = "jogando"
GOL = "gol"
FIM = "fim"
estado = MENU

# =====================================================================
#  FONTES (resolução cheia, ficam nítidas)
# =====================================================================
def carregar_fonte(tam, negrito=True):
    return pygame.font.SysFont("arial,helvetica,dejavusans,verdana", tam, bold=negrito)


f_mini = carregar_fonte(15)
f_pequena = carregar_fonte(21)
f_media = carregar_fonte(30)
f_grande = carregar_fonte(46)
f_placar = carregar_fonte(44)
f_titulo = carregar_fonte(104)
f_gol = carregar_fonte(120)
f_ad = pygame.font.SysFont("arial,helvetica,dejavusans", 9, bold=True)


def texto(sup, msg, fonte, cor, x, y, centro=False, sombra=(0, 0, 0),
          contorno=None, alpha=255):
    img = fonte.render(msg, True, cor)
    w, h = img.get_size()
    if centro:
        x -= w // 2
    if contorno:
        o = fonte.render(msg, True, contorno)
        if alpha < 255:
            o.set_alpha(alpha)
        for dx, dy in ((-3, 0), (3, 0), (0, -3), (0, 3),
                       (-2, -2), (2, 2), (-2, 2), (2, -2)):
            sup.blit(o, (x + dx, y + dy))
    elif sombra:
        s = fonte.render(msg, True, sombra)
        if alpha < 255:
            s.set_alpha(alpha)
        sup.blit(s, (x + 2, y + 3))
    if alpha < 255:
        img.set_alpha(alpha)
    sup.blit(img, (x, y))
    return w


def texto_zoom(sup, msg, fonte, cor, cx, cy, zoom, contorno=CONTORNO):
    img = fonte.render(msg, True, cor)
    o = fonte.render(msg, True, contorno)
    img = pygame.transform.rotozoom(img, 0, zoom)
    o = pygame.transform.rotozoom(o, 0, zoom)
    w, h = img.get_size()
    for dx, dy in ((-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3), (-3, 3), (3, -3), (0, 8)):
        sup.blit(o, (cx - w // 2 + dx, cy - h // 2 + dy))
    sup.blit(img, (cx - w // 2, cy - h // 2))


# =====================================================================
#  CAMPO
# =====================================================================
CAMPO = pygame.Rect(25, 65, 590, 300)
GOL_Y1, GOL_Y2 = 185, 245
TOPO_TRIB = 56
BASE_TRIB = 374


def escurecer(cor, f):
    return tuple(max(0, min(255, int(c * f))) for c in cor)


# =====================================================================
#  KITS DOS JOGADORES
# =====================================================================
def kit(camisa, calcao, meia, cabelo, pele, listra=None, luva=None):
    return dict(camisa=camisa, escura=escurecer(camisa, 0.72), calcao=calcao,
                calcao_esc=escurecer(calcao, 0.78), meia=meia, cabelo=cabelo,
                pele=pele, listra=listra, luva=luva)


PELES = [(236, 188, 145), (214, 160, 115), (160, 112, 76), (110, 74, 50)]
CABELOS = [(65, 40, 25), (25, 20, 20), (205, 160, 60), (130, 60, 30), (230, 225, 220)]

KIT_JOG = kit((40, 110, 230), (245, 245, 250), (40, 110, 230), CABELOS[0], PELES[0],
              listra=(255, 255, 255))
KIT_ADV = kit((215, 40, 45), (250, 250, 250), (215, 40, 45), CABELOS[1], PELES[1])
KIT_GOL_ADV = kit((255, 210, 40), (35, 35, 45), (35, 35, 45), CABELOS[1], PELES[2],
                  luva=(255, 140, 40))
KIT_GOL_NOSSO = kit((40, 190, 120), (35, 35, 45), (35, 35, 45), CABELOS[3], PELES[0],
                    luva=(255, 255, 255))


def variar(base, cabelo, pele, camisa=None):
    k = dict(base)
    k["cabelo"] = cabelo
    k["pele"] = pele
    if camisa:
        k["camisa"] = camisa
        k["escura"] = escurecer(camisa, 0.72)
        k["meia"] = camisa
    return k


# =====================================================================
#  SPRITES (pixel art gerada por código, com contorno e animação)
# =====================================================================
_cache_sprites = {}


def construir_sprite(k, frame):
    b = pygame.Surface((18, 28), pygame.SRCALPHA)

    def R(cor, r):
        pygame.draw.rect(b, cor, r)

    braco_e = braco_d = 0
    perna_e = perna_d = 6
    levantado = False
    if frame == 1:
        perna_e, perna_d, braco_e, braco_d = 5, 7, 1, -1
    elif frame == 2:
        perna_e, perna_d, braco_e, braco_d = 7, 5, -1, 1
    elif frame == 4:
        levantado = True

    # cabeça
    R(k["pele"], (5, 3, 8, 5))
    R(k["cabelo"], (5, 0, 8, 3))
    R(k["cabelo"], (4, 1, 1, 4))
    R(k["cabelo"], (5, 3, 2, 3))
    b.set_at((9, 5), (25, 25, 35))
    b.set_at((11, 5), (25, 25, 35))

    # braços
    cor_mao = k["luva"] or k["pele"]
    if levantado:
        for ax in (0, 16):
            R(k["camisa"], (ax, 6, 2, 3))
            R(cor_mao, (ax, 2, 2, 4))
    else:
        R(k["camisa"], (1, 9 + braco_e, 2, 4))
        R(cor_mao, (1, 13 + braco_e, 2, 3))
        R(k["camisa"], (15, 9 + braco_d, 2, 4))
        R(cor_mao, (15, 13 + braco_d, 2, 3))

    # tronco
    R(k["camisa"], (3, 8, 12, 8))
    R(k["escura"], (12, 8, 3, 8))
    R(k["escura"], (3, 15, 12, 1))
    if k["listra"]:
        for sx in (5, 8):
            R(k["listra"], (sx, 8, 2, 7))
    R((240, 240, 240), (7, 8, 4, 1))

    # calção
    R(k["calcao"], (4, 16, 10, 4))
    R(k["calcao_esc"], (9, 17, 1, 3))
    R(k["calcao_esc"], (13, 16, 1, 4))

    # pernas
    for lx, h in ((5, perna_e), (10, perna_d)):
        R(k["pele"], (lx, 20, 3, 2))
        R(k["meia"], (lx, 22, 3, max(1, h - 4)))
        R((28, 28, 34), (lx, 20 + h - 2, 4, 2))

    # contorno
    out = pygame.Surface((20, 30), pygame.SRCALPHA)
    try:
        m = pygame.mask.from_surface(b)
        sil = m.to_surface(setcolor=CONTORNO + (255,), unsetcolor=(0, 0, 0, 0))
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)):
            out.blit(sil, (1 + dx, 1 + dy))
    except Exception:
        pass
    out.blit(b, (1, 1))
    return out


def sprite(k, chave, frame, esq):
    c = (chave, frame, esq)
    if c not in _cache_sprites:
        s = construir_sprite(k, frame)
        if esq:
            s = pygame.transform.flip(s, True, False)
        _cache_sprites[c] = s
    return _cache_sprites[c]


# =====================================================================
#  ATORES
# =====================================================================
class Ator:
    def __init__(self, x, y, k, chave, esq=False):
        self.x = float(x)
        self.y = float(y)
        self.inicio = (float(x), float(y))
        self.kit = k
        self.chave = chave
        self.esq_inicial = esq
        self.esq = esq
        self.anim = random.random() * 4
        self.movendo = False
        self.pose = None
        self.timer_pose = 0.0
        self.dir = (-1.0, 0.0) if esq else (1.0, 0.0)
        self.defesa_cd = 0.0

    @property
    def cx(self):
        return self.x + 7

    @property
    def cy(self):
        return self.y + 9

    def reiniciar(self):
        self.x, self.y = self.inicio
        self.movendo = False
        self.pose = None
        self.timer_pose = 0
        self.esq = self.esq_inicial
        self.dir = (-1.0, 0.0) if self.esq else (1.0, 0.0)


def limitar(a):
    a.x = max(27, min(599, a.x))
    a.y = max(70, min(342, a.y))


POS_ADV = [(390, 110), (450, 170), (470, 270), (330, 145), (350, 300)]
POS_COMP = [(180, 110), (190, 290), (280, 150), (280, 270)]

jogador = Ator(100, 205, KIT_JOG, "jogador")
companheiros = [
    Ator(x, y, variar(KIT_JOG, CABELOS[(i + 1) % 5], PELES[(i + 2) % 4], (95, 165, 255)), f"c{i}")
    for i, (x, y) in enumerate(POS_COMP)
]
adversarios = [
    Ator(x, y, variar(KIT_ADV, CABELOS[(i * 2) % 5], PELES[(i + 1) % 4]), f"a{i}", esq=True)
    for i, (x, y) in enumerate(POS_ADV)
]
goleiro_adv = Ator(598, 208, KIT_GOL_ADV, "gadv", esq=True)
goleiro_nosso = Ator(28, 208, KIT_GOL_NOSSO, "gnos", esq=False)
goleiro_adv.vel = 95
goleiro_nosso.vel = 85
todos_atores = [jogador] + companheiros + adversarios + [goleiro_adv, goleiro_nosso]

tempo_desarmes = [0.0 for _ in adversarios]

# =====================================================================
#  ESTADO DA PARTIDA
# =====================================================================
bola_x, bola_y = 125.0, 215.0
bola_vx = bola_vy = 0.0
bola_z = bola_vz = 0.0
bola_giro = 0.0
gols = 0
gols_sofridos = 0
TEMPO_PARTIDA = 90
tempo_jogo = TEMPO_PARTIDA
tempo_chute = 0.0
bloqueio_controle = 0.0
tempo_gol = 0.0
gol_quem = None
tremor = 0.0
excitacao = 0.0
t_global = 0.0
t_partida = 0.0

particulas = []
popups = []


# =====================================================================
#  PARTÍCULAS E POPUPS
# =====================================================================
def particula(x, y, vx, vy, vida, cor, tam, grav=0.0):
    particulas.append([x, y, vx, vy, vida, vida, cor, tam, grav])


def atualizar_particulas(dt):
    for p in particulas:
        p[0] += p[2] * dt
        p[1] += p[3] * dt
        p[3] += p[8] * dt
        p[4] -= dt
    particulas[:] = [p for p in particulas if p[4] > 0]
    for q in popups:
        q[2] -= 22 * dt
        q[3] -= dt
    popups[:] = [q for q in popups if q[3] > 0]


def desenhar_particulas():
    for p in particulas:
        tam = max(1, int(round(p[7] * p[4] / p[5]))) if p[8] == 0 else p[7]
        pygame.draw.rect(jogo, p[6], (int(p[0]), int(p[1]), tam, tam))


def popup(msg, x, y, cor=BRANCO):
    popups.append([msg, x, y, 1.1, cor])


def poeira(x, y, n=3):
    for _ in range(n):
        particula(x + random.uniform(-3, 3), y, random.uniform(-14, 14),
                  random.uniform(-14, -2), random.uniform(0.25, 0.5),
                  (150, 185, 120), random.choice((2, 3)))


def confete(x, y, n, raio=130):
    cores = [(255, 210, 40), (255, 255, 255), (60, 150, 255), (255, 80, 80), (90, 230, 120)]
    for _ in range(n):
        ang = random.uniform(0, math.tau)
        v = random.uniform(30, raio)
        particula(x, y, math.cos(ang) * v, math.sin(ang) * v - 40,
                  random.uniform(1.2, 2.2), random.choice(cores), 2, grav=140)


def chuva_confete(n):
    cores = [(255, 210, 40), (255, 255, 255), (60, 150, 255), (255, 80, 80), (90, 230, 120)]
    for _ in range(n):
        particula(random.uniform(0, LARGURA), random.uniform(-20, 40),
                  random.uniform(-25, 25), random.uniform(30, 90),
                  random.uniform(1.6, 2.6), random.choice(cores), 2, grav=60)


# =====================================================================
#  CENÁRIO (pré-renderizado uma única vez)
# =====================================================================
def construir_fundo():
    f = pygame.Surface((LARGURA, ALTURA))
    f.fill((24, 60, 32))

    # ---------- arquibancada superior ----------
    for y in range(0, TOPO_TRIB):
        t = y / TOPO_TRIB
        pygame.draw.line(f, (30 + int(26 * t), 32 + int(26 * t), 50 + int(30 * t)),
                         (0, y), (LARGURA, y))
    for row in range(8):
        ry = 6 + row * 6
        pygame.draw.rect(f, (74, 78, 104), (0, ry + 3, LARGURA, 3))
    for x in range(0, LARGURA, 80):
        pygame.draw.rect(f, (22, 24, 38), (x, 0, 2, TOPO_TRIB))
    pygame.draw.rect(f, (12, 14, 24), (0, 0, LARGURA, 4))

    # ---------- arquibancada inferior ----------
    for y in range(BASE_TRIB, ALTURA):
        t = (ALTURA - y) / (ALTURA - BASE_TRIB)
        pygame.draw.line(f, (30 + int(26 * t), 32 + int(26 * t), 50 + int(30 * t)),
                         (0, y), (LARGURA, y))
    for row in range(3):
        ry = 378 + row * 7
        pygame.draw.rect(f, (74, 78, 104), (0, ry + 3, LARGURA, 3))
    for x in range(40, LARGURA, 80):
        pygame.draw.rect(f, (22, 24, 38), (x, BASE_TRIB, 2, ALTURA - BASE_TRIB))

    # ---------- torcida (corpos estáticos) ----------
    cores_torcida = [(40, 110, 230), (40, 110, 230), (215, 45, 45), (215, 45, 45),
                     (240, 240, 240), (255, 210, 40), (60, 60, 80), (40, 170, 110)]
    esp = []

    def torcida(y_inicial, linhas, espaco):
        for row in range(linhas):
            y = y_inicial + row * espaco
            for i in range(0, 92):
                x = 3 + (row % 2) * 3 + i * 7
                if x > LARGURA - 3 or random.random() < 0.07:
                    continue
                cor = random.choice(cores_torcida)
                pygame.draw.rect(f, cor, (x - 2, y, 5, 4))
                pygame.draw.rect(f, escurecer(cor, 0.7), (x - 2, y + 3, 5, 1))
                esp.append((x, y, random.choice(PELES), random.random() * 6.28))

    torcida(10, 8, 6)
    torcida(381, 3, 7)

    # ---------- placas de publicidade ----------
    anuncios = [("KICK", (220, 60, 50)), ("ARENA", (40, 120, 220)), ("PRO", (30, 160, 100)),
                ("GOAL!", (240, 180, 30)), ("SPORT", (130, 60, 200)), ("LIGA", (20, 140, 180)),
                ("FC", (230, 100, 40)), ("STAR", (50, 60, 160)), ("PLAY", (200, 40, 110)),
                ("CUP", (30, 170, 70))]
    for faixa_y, deslocamento in ((TOPO_TRIB, 0), (365, 4)):
        for i in range(10):
            nome, cor = anuncios[(i + deslocamento) % 10]
            pygame.draw.rect(f, cor, (i * 64, faixa_y, 64, 9))
            pygame.draw.rect(f, escurecer(cor, 0.6), (i * 64, faixa_y + 8, 64, 1))
            pygame.draw.rect(f, escurecer(cor, 0.6), (i * 64, faixa_y, 1, 9))
            img = f_ad.render(nome, False, (255, 255, 255))
            f.blit(img, (i * 64 + 32 - img.get_width() // 2, faixa_y))
    pygame.draw.line(f, (255, 255, 255), (0, TOPO_TRIB), (LARGURA, TOPO_TRIB))

    # ---------- entorno do gramado ----------
    pygame.draw.rect(f, (28, 78, 40), (0, 65, LARGURA, 300))
    for _ in range(1500):
        x = random.randint(0, LARGURA - 1)
        y = random.randint(65, 364)
        c = f.get_at((x, y))
        d = random.choice((-6, -3, 3, 5))
        f.set_at((x, y), (max(0, c[0] + d), max(0, c[1] + d), max(0, c[2] + d)))

    # ---------- gramado com faixas ----------
    ncol = 10
    larg = CAMPO.w // ncol
    for i in range(ncol):
        cor = (41, 133, 57) if i % 2 == 0 else (49, 148, 67)
        pygame.draw.rect(f, cor, (CAMPO.x + i * larg, CAMPO.y, larg, CAMPO.h))
    for _ in range(7000):
        x = random.randint(CAMPO.x + 1, CAMPO.right - 2)
        y = random.randint(CAMPO.y + 1, CAMPO.bottom - 2)
        c = f.get_at((x, y))
        d = random.choice((-7, -4, 4, 7))
        f.set_at((x, y), (max(0, c[0] + d), max(0, min(255, c[1] + d)), max(0, c[2] + d)))
        if random.random() < 0.4 and y + 1 < CAMPO.bottom:
            f.set_at((x, y + 1), (max(0, c[0] + d), max(0, min(255, c[1] + d)), max(0, c[2] + d)))

    # ---------- gols (fundo da rede) ----------
    for gx in (5, 615):
        pygame.draw.rect(f, (18, 48, 26), (gx, GOL_Y1, 20, GOL_Y2 - GOL_Y1))

    # ---------- linhas ----------
    pygame.draw.rect(f, LINHA, CAMPO, 2)
    pygame.draw.line(f, LINHA, (320, 65), (320, 365), 2)
    pygame.draw.circle(f, LINHA, (320, 215), 48, 2)
    pygame.draw.circle(f, LINHA, (320, 215), 3)

    pygame.draw.rect(f, LINHA, (25, 140, 80, 150), 2)
    pygame.draw.rect(f, LINHA, (25, 175, 35, 80), 2)
    pygame.draw.rect(f, LINHA, (535, 140, 80, 150), 2)
    pygame.draw.rect(f, LINHA, (580, 175, 35, 80), 2)

    pygame.draw.circle(f, LINHA, (85, 215), 3)
    pygame.draw.circle(f, LINHA, (555, 215), 3)

    # meia-lua das áreas
    pygame.draw.arc(f, LINHA, (85 - 38, 215 - 38, 76, 76), 0, 1.0, 2)
    pygame.draw.arc(f, LINHA, (85 - 38, 215 - 38, 76, 76), math.tau - 1.0, math.tau, 2)
    pygame.draw.arc(f, LINHA, (555 - 38, 215 - 38, 76, 76), math.pi - 1.0, math.pi + 1.0, 2)

    # escanteios
    pygame.draw.arc(f, LINHA, (25 - 8, 65 - 8, 16, 16), 3 * math.pi / 2, math.tau, 2)
    pygame.draw.arc(f, LINHA, (615 - 8, 65 - 8, 16, 16), math.pi, 3 * math.pi / 2, 2)
    pygame.draw.arc(f, LINHA, (25 - 8, 365 - 8, 16, 16), 0, math.pi / 2, 2)
    pygame.draw.arc(f, LINHA, (615 - 8, 365 - 8, 16, 16), math.pi / 2, math.pi, 2)

    # bandeirinhas de escanteio
    for bx, by in ((25, 65), (615, 65), (25, 365), (615, 365)):
        pygame.draw.rect(f, (240, 240, 240), (bx - 1, by - 8, 1, 8))
        pygame.draw.polygon(f, AMARELO, [(bx, by - 8), (bx + 5, by - 6), (bx, by - 4)])

    return f, esp


def construir_frente():
    fr = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for gx in (5, 615):
        for x in range(gx, gx + 21, 4):
            pygame.draw.line(fr, (255, 255, 255, 70), (x, GOL_Y1), (x, GOL_Y2))
        for y in range(GOL_Y1, GOL_Y2 + 1, 4):
            pygame.draw.line(fr, (255, 255, 255, 70), (gx, y), (gx + 20, y))
    # molduras do gol
    for gx, linha_x, fundo_x in ((5, 25, 4), (615, 615, 634)):
        pygame.draw.rect(fr, (235, 235, 240), (fundo_x, GOL_Y1 - 1, 2, GOL_Y2 - GOL_Y1 + 3))
        pygame.draw.rect(fr, (235, 235, 240), (gx, GOL_Y1 - 1, 20, 2))
        pygame.draw.rect(fr, (235, 235, 240), (gx, GOL_Y2, 20, 2))
        for py in (GOL_Y1, GOL_Y2):
            pygame.draw.circle(fr, (250, 250, 250), (linha_x, py), 3)
            pygame.draw.circle(fr, (110, 115, 130), (linha_x, py), 3, 1)
    return fr


def construir_vinheta():
    v = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    n = 60
    for i in range(n):
        a = int(150 * (1 - i / n) ** 2.2)
        pygame.draw.rect(v, (0, 0, 15, a), (i, i, LARGURA - 2 * i, ALTURA - 2 * i), 1)
    return v


def construir_luz():
    luz = pygame.Surface((LARGURA, ALTURA))
    for cx, cy in ((30, 70), (610, 70), (30, 360), (610, 360)):
        t = pygame.Surface((LARGURA, ALTURA))
        for r in range(260, 0, -5):
            v = int(22 * (1 - r / 260) ** 1.6)
            pygame.draw.circle(t, (v, v, int(v * 0.8)), (cx, cy), r)
        luz.blit(t, (0, 0), special_flags=pygame.BLEND_RGB_MAX)
    return luz


fundo, espectadores = construir_fundo()
frente = construir_frente()
vinheta = construir_vinheta()
luz = construir_luz()

# fundo desfocado para menu
_pequeno = pygame.transform.smoothscale(fundo, (80, 50))
fundo_menu = pygame.transform.smoothscale(_pequeno, (LARGURA, ALTURA))
_escuro = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
_escuro.fill((4, 14, 24, 150))
fundo_menu.blit(_escuro, (0, 0))


# =====================================================================
#  DESENHO DO MUNDO
# =====================================================================
def desenhar_torcida(t):
    exc = max(0.12, excitacao)
    for x, y, pele, fase in espectadores:
        off = int(round(math.sin(t * 7 * (0.6 + exc) + fase) * exc * 2.2))
        yy = y + off
        pygame.draw.rect(jogo, pele, (x - 1, yy - 3, 3, 3))
        if exc > 0.45 and math.sin(t * 9 + fase) > 0.2:
            pygame.draw.rect(jogo, pele, (x - 3, yy - 5, 1, 3))
            pygame.draw.rect(jogo, pele, (x + 3, yy - 5, 1, 3))


def frame_ator(a):
    if a.timer_pose > 0 and a.pose is not None:
        return a.pose
    if a.movendo:
        return (0, 1, 0, 2)[int(a.anim * 8) % 4]
    return 0


def desenhar_ator(a, t):
    if a is jogador:
        # anel de destaque embaixo do jogador controlado
        pygame.draw.ellipse(jogo, (255, 225, 70), (int(a.cx) - 10, int(a.y) + 17, 20, 8), 1)
    surf = sprite(a.kit, a.chave, frame_ator(a), a.esq)
    jogo.blit(surf, (int(a.x) - 3, int(a.y) - 7))
    if a is jogador:
        oy = int(math.sin(t * 6) * 1.5)
        cx = int(a.cx)
        y0 = int(a.y) - 15 + oy
        pygame.draw.polygon(jogo, CONTORNO, [(cx - 5, y0 - 1), (cx + 5, y0 - 1), (cx, y0 + 6)])
        pygame.draw.polygon(jogo, AMARELO, [(cx - 3, y0), (cx + 3, y0), (cx, y0 + 4)])


def desenhar_bola_em(sup, x, y, r, giro):
    pygame.draw.circle(sup, CONTORNO, (x, y), r + max(1, r // 5))
    pygame.draw.circle(sup, (205, 210, 222), (x, y), r)
    pygame.draw.circle(sup, (252, 252, 252), (x - max(1, r // 5), y - max(1, r // 5)), max(1, r - max(1, r // 5)))
    for k in range(3):
        ang = giro + k * 2.094
        px = x + math.cos(ang) * r * 0.52
        py = y + math.sin(ang) * r * 0.52
        pygame.draw.circle(sup, (28, 28, 40), (int(round(px)), int(round(py))), max(1, r // 4))
    pygame.draw.circle(sup, (255, 255, 255), (x - r // 2, y - r // 2), max(1, r // 6))


def desenhar_bola():
    desenhar_bola_em(jogo, int(bola_x), int(bola_y - bola_z), 5, bola_giro)


def desenhar_partida(t):
    jogo.blit(fundo, (0, 0))
    desenhar_torcida(t)

    # sombras
    camada_sombra.fill((0, 0, 0, 0))
    for a in todos_atores:
        pygame.draw.ellipse(camada_sombra, (0, 0, 0, 75), (int(a.cx) - 8, int(a.y) + 18, 17, 6))
    escala = max(0.4, 1 - bola_z / 90)
    sw, sh = int(10 * escala), int(4 * escala)
    pygame.draw.ellipse(camada_sombra, (0, 0, 0, int(90 * escala)),
                        (int(bola_x) - sw // 2 + 1, int(bola_y) + 3, max(2, sw), max(2, sh)))
    jogo.blit(camada_sombra, (0, 0))

    # personagens e bola ordenados por profundidade
    itens = [(a.y + 21, 0, a) for a in todos_atores]
    itens.append((bola_y + 5, 1, None))
    itens.sort(key=lambda i: i[0])
    for _, tipo, obj in itens:
        if tipo == 0:
            desenhar_ator(obj, t)
        else:
            desenhar_bola()

    jogo.blit(frente, (0, 0))
    desenhar_particulas()
    jogo.blit(luz, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    jogo.blit(vinheta, (0, 0))


# =====================================================================
#  INTERFACE
# =====================================================================
def desenhar_hud():
    # painel do placar
    x0, y0, w, h = 320, 8, 640, 68
    pygame.draw.rect(ui, (10, 14, 28, 235), (x0, y0, w, h), border_radius=20)
    pygame.draw.rect(ui, (*AZUL_UI, 245), (x0, y0, 230, h),
                     border_top_left_radius=20, border_bottom_left_radius=20)
    pygame.draw.rect(ui, (*VERMELHO_UI, 245), (x0 + w - 230, y0, 230, h),
                     border_top_right_radius=20, border_bottom_right_radius=20)
    pygame.draw.rect(ui, (255, 255, 255, 70), (x0, y0, w, h), 2, border_radius=20)

    texto(ui, "VOCÊ", f_media, BRANCO, x0 + 24, y0 + 17)
    texto(ui, str(gols), f_placar, BRANCO, x0 + 184, y0 + 9, centro=True)
    texto(ui, "ADV.", f_media, BRANCO, x0 + w - 24 - f_media.size("ADV.")[0], y0 + 17)
    texto(ui, str(gols_sofridos), f_placar, BRANCO, x0 + w - 184, y0 + 9, centro=True)

    minuto = int(TEMPO_PARTIDA - tempo_jogo)
    texto(ui, f"{minuto}'", f_grande, AMARELO, 640, y0 + 8, centro=True)

    # barra de progresso
    prog = 1 - tempo_jogo / TEMPO_PARTIDA
    pygame.draw.rect(ui, (10, 14, 28, 200), (x0 + 40, y0 + h + 6, w - 80, 7), border_radius=4)
    if prog > 0:
        pygame.draw.rect(ui, (*AMARELO, 255), (x0 + 40, y0 + h + 6, int((w - 80) * prog), 7),
                         border_radius=4)

    # dicas de controle no começo da partida
    if t_partida < 8 and estado == JOGANDO:
        a = 255 if t_partida < 6 else int(255 * (8 - t_partida) / 2)
        painel = pygame.Surface((760, 46), pygame.SRCALPHA)
        pygame.draw.rect(painel, (8, 12, 24, int(210 * a / 255)), (0, 0, 760, 46), border_radius=14)
        ui.blit(painel, (260, 726))
        texto(ui, "WASD / SETAS mover   ·   SHIFT correr   ·   ESPAÇO chutar", f_pequena,
              BRANCO, 640, 736, centro=True, alpha=a)

    # textos flutuantes
    for msg, x, y, vida, cor in popups:
        a = int(255 * min(1, vida / 0.5))
        texto(ui, msg, f_pequena, cor, int(x * E), int(y * E), centro=True,
              contorno=CONTORNO, alpha=a)


def desenhar_banner_gol(t):
    faixa = pygame.Surface((LARGURA * E, 150), pygame.SRCALPHA)
    faixa.fill((0, 0, 0, 130))
    ui.blit(faixa, (0, 250))
    if gol_quem == "jogador":
        zoom = 0.9 + 0.12 * abs(math.sin(t * 7))
        texto_zoom(ui, "GOOOL!", f_gol, AMARELO, 640, 330, zoom)
        texto(ui, "VOCÊ MARCOU!", f_pequena, BRANCO, 640, 385, centro=True, alpha=230)
    else:
        zoom = 0.7 + 0.05 * abs(math.sin(t * 6))
        texto_zoom(ui, "GOL DO ADVERSÁRIO", f_gol, (255, 100, 100), 640, 330, zoom * 0.62)


def desenhar_fim():
    ov = pygame.Surface((LARGURA * E, ALTURA * E), pygame.SRCALPHA)
    ov.fill((4, 8, 18, 185))
    ui.blit(ov, (0, 0))
    px, py, pw, ph = 330, 150, 620, 500
    pygame.draw.rect(ui, (18, 24, 44, 245), (px, py, pw, ph), border_radius=26)
    pygame.draw.rect(ui, (255, 255, 255, 60), (px, py, pw, ph), 3, border_radius=26)

    texto(ui, "FIM DE JOGO", f_grande, BRANCO, 640, py + 30, centro=True)

    if gols > gols_sofridos:
        res, cor = "VITÓRIA!", (90, 230, 120)
    elif gols == gols_sofridos:
        res, cor = "EMPATE", AMARELO
    else:
        res, cor = "DERROTA", (255, 95, 95)
    texto(ui, res, f_titulo, cor, 640, py + 100, centro=True, contorno=CONTORNO)

    # placar
    pygame.draw.rect(ui, (*AZUL_UI, 255), (px + 110, py + 260, 150, 110), border_radius=18)
    pygame.draw.rect(ui, (*VERMELHO_UI, 255), (px + pw - 260, py + 260, 150, 110), border_radius=18)
    texto(ui, str(gols), f_gol, BRANCO, px + 185, py + 245, centro=True, sombra=(0, 0, 0))
    texto(ui, str(gols_sofridos), f_gol, BRANCO, px + pw - 185, py + 245, centro=True)
    texto(ui, "X", f_grande, AMARELO, 640, py + 288, centro=True)
    texto(ui, "VOCÊ", f_pequena, (190, 210, 255), px + 185, py + 375, centro=True)
    texto(ui, "ADVERSÁRIO", f_pequena, (255, 190, 190), px + pw - 185, py + 375, centro=True)

    texto(ui, "R  -  JOGAR NOVAMENTE", f_media, AMARELO, 640, py + 425, centro=True)
    texto(ui, "ESC  -  SAIR", f_pequena, (190, 195, 210), 640, py + 465, centro=True)


def desenhar_menu(t):
    jogo.blit(fundo_menu, (0, 0))
    jogo.blit(vinheta, (0, 0))
    jogo.blit(vinheta, (0, 0))
    pygame.transform.scale(jogo, (LARGURA * E, ALTURA * E), grande)
    tela.blit(grande, (0, 0))

    # título
    texto_zoom(ui, "FOOTBALL", f_titulo, BRANCO, 640, 150, 1.0, contorno=(10, 60, 30))
    texto_zoom(ui, "CAREER", f_titulo, AMARELO, 640, 262, 1.0, contorno=(10, 60, 30))

    # jogadores decorativos
    frame = (0, 1, 0, 2)[int(t * 6) % 4]
    spr_j = pygame.transform.scale(sprite(KIT_JOG, "jogador", frame, False), (120, 180))
    spr_a = pygame.transform.scale(sprite(adversarios[0].kit, adversarios[0].chave, frame, True), (120, 180))
    sombra = pygame.Surface((140, 36), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 110), (0, 0, 140, 36))
    ui.blit(sombra, (140, 506))
    ui.blit(sombra, (980, 506))
    ui.blit(spr_j, (150, 345))
    ui.blit(spr_a, (990, 345))

    # bola quicando
    quique = abs(math.sin(t * 3.2))
    by = 470 - int(quique * 70)
    sw = int(60 * (1 - quique * 0.4))
    sh = pygame.Surface((sw, 14), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (0, 0, 0, 100), (0, 0, sw, 14))
    ui.blit(sh, (640 - sw // 2, 510))
    desenhar_bola_em(ui, 640, by, 24, t * 4)

    # chamada
    a = int(150 + 105 * math.sin(t * 4))
    texto(ui, "PRESSIONE ENTER", f_grande, AMARELO, 640, 565, centro=True, alpha=a)
    texto(ui, "WASD ou SETAS  -  movimentar", f_pequena, BRANCO, 640, 650, centro=True)
    texto(ui, "SHIFT  -  correr      ESPAÇO  -  chutar", f_pequena, BRANCO, 640, 685, centro=True)
    texto(ui, "ESC  -  sair", f_mini, (170, 180, 195), 640, 735, centro=True)


# =====================================================================
#  LÓGICA
# =====================================================================
def reiniciar_bola():
    global bola_x, bola_y, bola_vx, bola_vy, bola_z, bola_vz
    bola_x, bola_y = 125.0, 215.0
    bola_vx = bola_vy = 0.0
    bola_z = bola_vz = 0.0
    for a in todos_atores:
        a.reiniciar()
    for i in range(len(tempo_desarmes)):
        tempo_desarmes[i] = 0
    particulas.clear()


def movimentar_jogador(dt):
    teclas = pygame.key.get_pressed()
    corre = teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
    vel = 160 if corre else 115

    dx = dy = 0
    if teclas[pygame.K_w] or teclas[pygame.K_UP]:
        dy -= 1
    if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
        dy += 1
    if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
        dx -= 1
    if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
        dx += 1

    if dx or dy:
        n = math.hypot(dx, dy)
        dx /= n
        dy /= n
        jogador.x += dx * vel * dt
        jogador.y += dy * vel * dt
        jogador.dir = (dx, dy)
        if dx:
            jogador.esq = dx < 0
        jogador.movendo = True
        jogador.anim += dt * (1.5 if corre else 1.0)
        if corre and random.random() < 0.35:
            poeira(jogador.cx - dx * 4, jogador.y + 21, 1)
    else:
        jogador.movendo = False
    limitar(jogador)


def movimentar_companheiros(dt):
    offsets = [(-55, -65), (-55, 65), (45, -75), (45, 75)]
    for i, a in enumerate(companheiros):
        alvo_x = max(40, min(585, jogador.x + offsets[i][0]))
        alvo_y = max(75, min(345, jogador.y + offsets[i][1]))
        dx = alvo_x - a.x
        dy = alvo_y - a.y
        d = math.hypot(dx, dy)
        if d > 5:
            a.x += dx / d * 75 * dt
            a.y += dy / d * 75 * dt
            a.movendo = True
            a.anim += dt
            if abs(dx) > 1:
                a.esq = dx < 0
        else:
            a.movendo = False
            a.esq = jogador.esq
        limitar(a)


def movimentar_adversarios(dt):
    global bola_vx, bola_vy, bola_vz, bloqueio_controle
    for i, a in enumerate(adversarios):
        dx = bola_x - a.cx
        dy = bola_y - a.cy
        d = math.hypot(dx, dy)
        vx = vy = 0.0
        if d > 0:
            if i == 0 or d < 110:
                if d > 6:
                    vx, vy = dx / d * 85, dy / d * 85
            else:
                dxj = jogador.cx - a.cx
                dyj = jogador.cy - a.cy
                dj = math.hypot(dxj, dyj)
                if dj > 65:
                    vx, vy = dxj / dj * 55, dyj / dj * 55
        a.x += vx * dt
        a.y += vy * dt
        a.movendo = (abs(vx) + abs(vy)) > 1
        if abs(vx) > 1:
            a.esq = vx < 0
        if a.movendo:
            a.anim += dt
        limitar(a)

        # tentativa de desarme
        tempo_desarmes[i] -= dt
        dj = math.hypot(jogador.cx - a.cx, jogador.cy - a.cy)
        if dj < 17 and tempo_desarmes[i] <= 0:
            db = math.hypot(bola_x - a.cx, bola_y - a.cy)
            if db < 35:
                bola_vx = -180
                bola_vy = 0
                bola_vz = 90
                bloqueio_controle = 0.5
                tempo_desarmes[i] = 1.5
                a.pose = 1
                a.timer_pose = 0.25
                poeira(a.cx, a.y + 20, 6)
                popup("DESARME!", a.cx, a.y - 14, (255, 130, 120))


def movimentar_goleiros(dt):
    global bola_vx, bola_vy, bola_vz, bloqueio_controle, tremor
    for g, lado in ((goleiro_adv, 1), (goleiro_nosso, -1)):
        na_area = bola_x > 330 if lado == 1 else bola_x < 310
        alvo = bola_y if na_area else 215
        alvo = max(201, min(229, alvo))
        passo = g.vel * dt
        mov = max(-passo, min(passo, alvo - g.cy))
        g.y += mov
        g.movendo = abs(mov) > 0.15
        if g.movendo:
            g.anim += dt
        g.esq = lado == 1
        g.defesa_cd -= dt

        # braços para cima quando a bola vem forte
        if math.hypot(bola_x - g.cx, bola_y - g.cy) < 70 and math.hypot(bola_vx, bola_vy) > 150:
            g.pose = 4
            g.timer_pose = max(g.timer_pose, 0.12)

        hit = pygame.Rect(0, 0, 18, 34)
        hit.center = (int(g.cx), int(g.cy))
        if g.defesa_cd <= 0 and hit.inflate(8, 8).collidepoint(bola_x, bola_y):
            if lado == 1:
                bola_vx = -(abs(bola_vx) * 0.6 + 110)
            else:
                bola_vx = abs(bola_vx) * 0.6 + 110
            bola_vy += random.uniform(-90, 90)
            bola_vz = 90
            g.defesa_cd = 0.5
            g.pose = 4
            g.timer_pose = 0.4
            bloqueio_controle = 0.35
            tremor = max(tremor, 0.15)
            popup("DEFESA!", g.cx, g.y - 16, (255, 235, 120))
            confete(bola_x, bola_y, 8, 60)


def controlar_bola(dt):
    global bola_x, bola_y, bola_vx, bola_vy, bola_z, bola_vz, bola_giro
    px, py = bola_x, bola_y
    teclas = pygame.key.get_pressed()
    dist = math.hypot(bola_x - jogador.cx, bola_y - jogador.cy)
    vel = math.hypot(bola_vx, bola_vy)

    # condução: a bola gruda nos pés, na direção em que o jogador corre
    if dist < 24 and not teclas[pygame.K_SPACE] and bloqueio_controle <= 0 \
            and vel < 320 and bola_z < 6:
        ax = jogador.cx + jogador.dir[0] * 13
        ay = jogador.y + 18 + jogador.dir[1] * 10
        k = min(1.0, 16 * dt)
        bola_x += (ax - bola_x) * k
        bola_y += (ay - bola_y) * k
        bola_vx *= 0.6
        bola_vy *= 0.6

    # física
    bola_x += bola_vx * dt
    bola_y += bola_vy * dt
    atrito = 0.985 ** (dt * 60)
    bola_vx *= atrito
    bola_vy *= atrito
    if abs(bola_vx) < 2:
        bola_vx = 0
    if abs(bola_vy) < 2:
        bola_vy = 0

    # altura da bola (efeito visual)
    if bola_z > 0 or bola_vz != 0:
        bola_vz -= 560 * dt
        bola_z += bola_vz * dt
        if bola_z <= 0:
            bola_z = 0
            bola_vz = -bola_vz * 0.4 if abs(bola_vz) > 70 else 0

    # bordas
    if bola_y < 70:
        bola_y = 70
        bola_vy = abs(bola_vy)
    if bola_y > 360:
        bola_y = 360
        bola_vy = -abs(bola_vy)
    if bola_x < 25 and not (GOL_Y1 < bola_y < GOL_Y2):
        bola_x = 25
        bola_vx = abs(bola_vx)
    if bola_x > 615 and not (GOL_Y1 < bola_y < GOL_Y2):
        bola_x = 615
        bola_vx = -abs(bola_vx)
    if bola_x > 615 or bola_x < 25:
        bola_y = max(GOL_Y1 + 5, min(GOL_Y2 - 5, bola_y))

    # rotação e rastro
    bola_giro += math.hypot(bola_x - px, bola_y - py) * 0.35
    if vel > 200 and random.random() < 0.8:
        particula(bola_x, bola_y - bola_z, random.uniform(-6, 6), random.uniform(-6, 6),
                  0.25, (235, 242, 235), 3)


def chutar():
    global bola_vx, bola_vy, bola_vz, bloqueio_controle
    dist = math.hypot(bola_x - jogador.cx, bola_y - jogador.cy)
    if dist < 38:
        dx, dy = jogador.dir
        n = math.hypot(dx, dy)
        if n < 0.01:
            dx, dy = bola_x - jogador.cx, bola_y - jogador.cy
            n = max(1, math.hypot(dx, dy))
        bola_vx = dx / n * 390
        bola_vy = dy / n * 390
        bola_vz = 150
        bloqueio_controle = 0.3
        jogador.pose = 1
        jogador.timer_pose = 0.18
        for _ in range(8):
            particula(bola_x, bola_y, random.uniform(-45, 45), random.uniform(-45, 45),
                      random.uniform(0.2, 0.4), random.choice(((150, 185, 120), (255, 255, 255))), 2)


def marcou(quem):
    global gols, gols_sofridos, estado, tempo_gol, gol_quem, tremor, excitacao
    estado = GOL
    tempo_gol = 2.6
    gol_quem = quem
    tremor = 0.5
    excitacao = 1.0
    if quem == "jogador":
        gols += 1
        confete(bola_x, bola_y, 70)
        chuva_confete(90)
        for a in [jogador] + companheiros:
            a.pose = 4
            a.timer_pose = tempo_gol
    else:
        gols_sofridos += 1
        for a in adversarios:
            a.pose = 4
            a.timer_pose = tempo_gol
    for a in todos_atores:
        a.movendo = False


def verificar_gols():
    if bola_x > 620 and GOL_Y1 < bola_y < GOL_Y2:
        marcou("jogador")
    elif bola_x < 20 and GOL_Y1 < bola_y < GOL_Y2:
        marcou("adv")


def atualizar_atores(dt):
    for a in todos_atores:
        a.timer_pose -= dt


def atualizar_jogo(dt):
    global tempo_chute, bloqueio_controle, tempo_jogo, estado, t_partida
    tempo_chute -= dt
    bloqueio_controle -= dt
    t_partida += dt
    tempo_jogo -= dt
    if tempo_jogo <= 0:
        tempo_jogo = 0
        estado = FIM
        return
    movimentar_jogador(dt)
    movimentar_companheiros(dt)
    movimentar_adversarios(dt)
    movimentar_goleiros(dt)
    controlar_bola(dt)
    verificar_gols()


def atualizar_gol(dt):
    global tempo_gol, bola_x, bola_y, bola_vx, bola_vy, bola_z, bola_vz, estado
    tempo_gol -= dt
    bola_x += bola_vx * dt
    bola_y += bola_vy * dt
    f = 0.9 ** (dt * 60)
    bola_vx *= f
    bola_vy *= f
    if gol_quem == "jogador":
        if bola_x > 632:
            bola_x = 632
            bola_vx = -abs(bola_vx) * 0.3
    else:
        if bola_x < 8:
            bola_x = 8
            bola_vx = abs(bola_vx) * 0.3
    bola_y = max(GOL_Y1 + 5, min(GOL_Y2 - 5, bola_y))
    if bola_z > 0 or bola_vz != 0:
        bola_vz -= 560 * dt
        bola_z += bola_vz * dt
        if bola_z <= 0:
            bola_z = 0
            bola_vz = 0
    if gol_quem == "jogador" and random.random() < 0.15:
        chuva_confete(3)
    if tempo_gol <= 0:
        reiniciar_bola()
        estado = JOGANDO


def nova_partida():
    global gols, gols_sofridos, tempo_jogo, t_partida, tempo_chute, bloqueio_controle
    gols = 0
    gols_sofridos = 0
    tempo_jogo = TEMPO_PARTIDA
    t_partida = 0
    tempo_chute = 0
    bloqueio_controle = 0
    popups.clear()
    reiniciar_bola()


# =====================================================================
#  LOOP PRINCIPAL
# =====================================================================
rodando = True

while rodando:
    dt = min(relogio.tick(60) / 1000, 0.05)
    t_global += dt

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        if evento.type == pygame.KEYDOWN:
            if estado == MENU:
                if evento.key == pygame.K_RETURN:
                    estado = JOGANDO
                elif evento.key == pygame.K_ESCAPE:
                    rodando = False

            elif estado == JOGANDO:
                if evento.key == pygame.K_SPACE and tempo_chute <= 0:
                    chutar()
                    tempo_chute = 0.45
                if evento.key == pygame.K_ESCAPE:
                    estado = MENU

            elif estado == FIM:
                if evento.key == pygame.K_r:
                    nova_partida()
                    estado = JOGANDO
                if evento.key == pygame.K_ESCAPE:
                    rodando = False

    ui.fill((0, 0, 0, 0))

    if estado == MENU:
        desenhar_menu(t_global)
        tela.blit(ui, (0, 0))
    else:
        if estado == JOGANDO:
            atualizar_jogo(dt)
        elif estado == GOL:
            atualizar_gol(dt)
        atualizar_atores(dt)
        atualizar_particulas(dt)
        excitacao = max(0.0, excitacao - 0.35 * dt)
        tremor = max(0.0, tremor - dt)

        desenhar_partida(t_global)

        pygame.transform.scale(jogo, (LARGURA * E, ALTURA * E), grande)
        ox = oy = 0
        if tremor > 0:
            amp = 10 * tremor
            ox = int(random.uniform(-amp, amp))
            oy = int(random.uniform(-amp, amp))
        tela.fill((0, 0, 0))
        tela.blit(grande, (ox, oy))

        desenhar_hud()
        if estado == GOL:
            desenhar_banner_gol(t_global)
        if estado == FIM:
            desenhar_fim()
        tela.blit(ui, (0, 0))

    pygame.display.flip()

pygame.quit()
sys.exit()