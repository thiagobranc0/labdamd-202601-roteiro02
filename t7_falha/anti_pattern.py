# anti_pattern.py — transparencia excessiva: parece uma chamada local
def get_user(user_id: int) -> dict:
    # Simula uma chamada a banco de dados que parece local mas e remota
    # O chamador nao tem como saber que isso pode:
    #  - Levar 800ms (latencia de rede)
    #  - Lancar TimeoutError (rede caiu)
    #  - Retornar None silenciosamente e causar KeyError adiante
    pass  # db.query(...) seria aqui

# Problema: parece uma funcao local mas tem todos os riscos de rede
# user = get_user(42)
# print(user["name"])   # KeyError silencioso se user for None!

print("Este arquivo demonstra o ANTI-PATTERN de transparencia excessiva.")
print("Veja bom_pattern.py para a solucao correta.")
