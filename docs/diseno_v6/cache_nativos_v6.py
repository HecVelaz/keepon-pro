"""Actualiza una entrada sin perder el resto de un lote CAD ya verificado."""


def actualizar_pieza(previas, nueva):
    return [p for p in previas if p['archivo'] != nueva['archivo']] + [nueva]
