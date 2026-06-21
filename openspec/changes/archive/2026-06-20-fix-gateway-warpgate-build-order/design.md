## Context

The bot's build pipeline has four interacting methods in `src/bot/core.py`:

- `manage_early_game()` (line 432): Phase machine for the first build order (Pylon→Gateway→CyberCore→Warpgate). Currently hard-stops at `self.time >= 90`.
- `manage_gas()` (line 628): Builds Assimilators and assigns gas workers. Gates second Assimilator on `GATEWAY.amount > 0`.
- `manage_tech()` (line 687): Emergency Gateway fallback, CyberCore prerequisite, Warpgate Research, and tech structure expansion. Uses `GATEWAY`-only checks in three places.
- `manage_army()` (line 916): Trains from Gateways and warps from Warpgates. Gateways loop already correct, but the emergency build interference prevents it from ever running successfully.

All four methods use `self.structures(UnitTypeId.GATEWAY).amount` to determine if a Gateway exists. After Warpgate Research, Gateways auto-convert to Warpgates in SC2, making `GATEWAY.amount` permanently zero. This causes three distinct failure modes:

1. `manage_tech()` emergency builds Gateways in an infinite loop (line 691–697)
2. `manage_gas()` gate on second Assimilator never lifts (line 629)
3. `manage_army()` Gateway training loop becomes dead code (line 937)

Additionally, `manage_gas()` builds the first Assimilator before the Pylon exists because there is no Pylon prerequisite check.

## Goals / Non-Goals

**Goals:**
- Make `manage_tech()` treat Warpgates as equivalent to Gateways for prerequisite and emergency checks
- Make `manage_gas()` treat Warpgates as equivalent to Gateways for the second-assimilator gate
- Add Pylon prerequisite to `manage_gas()` so it does not build an Assimilator before the first Pylon
- Allow `manage_early_game()` to continue beyond t=90 until all phases complete
- Ensure `manage_army()` Gateway training loop checks combined Gateway+Warpgate count

**Non-Goals:**
- Changing the strategy engine or bias calculator
- Altering unit production logic beyond the Gateway/Warpgate detection fix
- Adding new unit types or build order phases
- Changing timeout durations or expansion logic

## Decisions

### D1: Introducir helper `_gateway_count()` como lectura combinada

En lugar de repetir `GATEWAY.amount + WARPGATE.amount` en 6 lugares distintos, se introduce un helper privado:

```python
def _gateway_count(self) -> int:
    return (self.structures(UnitTypeId.GATEWAY).amount +
            self.structures(UnitTypeId.WARPGATE).amount)
```

**Alternativa considerada**: Hacer el reemplazo inline en cada sitio. Rechazada porque la intención semántica ("¿tenemos producción de Gateway/Warpgate?") se repite 6+ veces y es propensa a divergencia futura.

### D2: manage_early_game() remueve `t >= 90` hard-stop

Se elimina la condición `if self.time >= 90: return`. Las fases ya tienen timeout de 15s cada una. Si una fase falla, se salta. Si todas las fases se completan, el método naturalmente no hace nada más (todas las condiciones son "if amount == 0"). El resultado es que el early game sigue intentando hasta completarse, no hasta que pasa un timer arbitrario.

**Alternativa considerada**: Extender el timer a 180s. Rechazada porque no resuelve el problema de raíz; el momento en que se completa el early game depende de la velocidad de build de cada mapa/raza, no de un timer fijo.

### D3: manage_gas() añade prerequisito de Pylon

Se añade al inicio de `manage_gas()` una guarda:
```python
if self.structures(UnitTypeId.PYLON).amount == 0:
    return
```
Esto garantiza que el build order correcto sea Pylon → Gateway → Assimilator, no Assimilator → Pylon → Gateway.

**Alternativa considerada**: Mover `manage_gas()` después de `manage_pylons()` en `on_step()`. Rechazada porque ya está en ese orden pero el problema es que `manage_gas` no respeta el orden — construir el Assimilator antes del Pylon es válido en SC2 (no requiere Pylon), pero es subóptimo como build order.

### D4: manage_gas() usa `_gateway_count()` para el gate de segundo Assimilator

Línea 629 cambia de `self.structures(UnitTypeId.GATEWAY).amount == 0` a `self._gateway_count() == 0`.

### D5: manage_tech() usa `_gateway_count()` en todos los checks de Gateway

Tres sitios:
- Línea 691: Emergency Gateway fallback (`_gateway_count() == 0`)
- Línea 719: Target gateway count (ya usa `self.structures(UnitTypeId.GATEWAY)`, se cambia a `self.structures(UnitTypeId.GATEWAY).amount + self.structures(UnitTypeId.WARPGATE).amount`)
- El check implícito de "si no hay Gateway, construir CyberCore" en línea 699 no necesita cambio porque `CYBERNETICSCORE.amount == 0` ya es correcto

### D6: manage_army() Gateway training loop usa `_gateway_count()` para early-exit

Se añade una guarda temprana: si no hay Gateways ni Warpgates, no intentar entrenar. El loop de Warpgates en línea 943 ya es correcto.

## Risks / Trade-offs

- **[Risk] El cambio en manage_early_game() podría causar que fases tempranas se reintenten indefinidamente si fallan por razones no recuperables** → Mitigación: Los timeouts de 15s por fase se mantienen. Si una fase no puede completarse, se salta después de 15s exactamente como ahora.
- **[Risk] `_gateway_count()` podría incluir Gateways/Warpgates en construcción que no están listos para producir** → Mitigación: Solo se usa para checks de existencia ("¿hay alguno?"), no para producción. La producción sigue usando `.ready.idle` como antes.
