## Context

El bot MyBot (Protoss) usa `manage_tech()` para construir todas las estructuras. El metodo recibe un `action` del strategy engine (`PriorityEngine`) que evalua formulas YAML para recomendar la mejor accion. Pero `manage_tech` procesa el action ANTES de verificar si hay Gateway, causando un early return si el action recomienda Forge/Twilight/Robo/Stargate. Esto deja al bot sin produccion militar acumulando recursos. Ademas, `manage_gas` compite por workers con la construccion del Gateway.

## Goals / Non-Goals

**Goals:**
- Garantizar que el bot SIEMPRE construya Pylon → Gateway → Cyber Core → Warp Gate antes de cualquier tech
- Prevenir que el strategy engine recomiende estructuras sin prerequisitos de produccion
- Diagnosticar fallos de construccion con logging explicito
- Evitar que `manage_gas` bloquee la construccion del Gateway
- Expansiones mas agresivas via mineral banking

**Non-Goals:**
- No cambiar la FSM del decision engine (DEFEND/ATTACK/RECOVER)
- No modificar el sistema de scouting
- No cambiar la produccion de unidades ni el army management
- No modificar el sistema de upgrades (solo los prerequisitos en formulas)

## Decisions

### 1. `manage_early_game()` como metodo separado vs integrado en `manage_tech`

**Elegido**: Metodo separado, ejecutado ANTES de `manage_tech` en `on_step`.

La separacion mantiene las responsabilidades claras: `manage_early_game` es deterministico y acotado en tiempo (~90s), mientras `manage_tech` sigue siendo flexible post-early-game. Si `manage_early_game` se integrara en `manage_tech`, el codigo seria mas dificil de testear y razonar, con condiciones mezcladas.

### 2. Build order con reintentos vs one-shot

**Elegido**: Cada fase retorna inmediatamente despues de ordenar su build, reintentando en el proximo step si falla. Timeout de 15s por fase.

Alternativa rechazada: intentar construir todo en un solo step (rompe el modelo async de SC2 y causa race conditions con workers).

### 3. `_build_if_able()` como helper reutilizable

**Elegido**: Metodo helper que encapsula `can_afford` → `find_placement` → `build` → `log`. Retorna `bool` y loguea el motivo de fallo.

Evita duplicacion en `manage_early_game`, `manage_tech`, y potencialmente `manage_upgrades`.

### 4. Prerequisitos en formulas YAML

**Elegido**: Multiplicar por `has_structure('GATEWAY')` o `has_structure('CYBERNETICSCORE')` como factor 0 en las formulas de Forge, Robo, Stargate, Twilight.

Esto hace que el score sea 0 cuando falta el prerequisito, y el strategy engine naturalmente elige otras acciones (como GATEWAY). Es mas elegante que hardcodear excepciones en el codigo.

### 5. `manage_gas`: limitar a 1 assimilator antes de Gateway

**Elegido**: Skip del segundo+ assimilator si no hay Gateway. El check es: `if self.structures(GATEWAY).amount == 0 and self.gas_buildings.amount >= 1: return`.

Esto evita que workers se vayan a gas en lugar de construir el Gateway, sin requerir cambios complejos en `manage_gas`.

### 6. Expansiones con mineral banking

**Elegido**: `if minerals > 400 and not already_pending(NEXUS): expand_now()`, manteniendo el check de saturacion 0.9 para el comportamiento normal.

Alternativa: bajar el umbral de saturacion. Pero el mineral banking es mas robusto porque captura el caso exacto donde el bot tiene recursos pero no expande.

## Risks / Trade-offs

- **[Build order demasiado rigido]**: Si el mapa es inusual o hay cheese del enemigo, el build order fijo de 90s podria ser suboptimo. → Mitigacion: el timeout de 15s por fase permite saltar fases si `find_placement` falla persistentemente (ej: mapa bloqueado).
- **[Formulas con factor 0 rompen el scoring]**: Si TODAS las formulas dan 0, el strategy engine retorna NOOP. → Mitigacion: `manage_early_game` cubre el early game. Post-early-game, siempre hay al menos GATEWAY con score > 0.
- **[manage_gas skip puede retrasar economia]**: Limitar a 1 assimilator antes de Gateway podria retrasar el gas inicial. → Mitigacion: el build order construye Gateway en ~22s, el retraso es minimo (unos pocos segundos de gas).
- **[Compatibilidad con perfiles custom]**: Si un usuario crea un perfil YAML sin los prerequisitos, el bot podria volver al bug original. → Mitigacion: documentar en el YAML los prerequisitos esperados. El `manage_early_game` sigue siendo el fallback deterministico.
