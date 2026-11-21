# 0.6.0 privacy risk disposition — review draft

**NOT a release approval.** 0.5.0 remains published. This document
records proposed scope and required evidence for #53/#92. Review the
exact corrective PR and then the final promotion SHA and distributions.
Do not infer an accepted final risk decision from this draft.

## Package-controlled gates

| ID | Ownership / impact | Proposed action and verification | Disposition |
|---|---|---|---|
| P1 | Package; credential-header classification, confidentiality | Inspect every Authorization/Cookie occurrence; retain default bypass before backend reads/writes. Test synthetic duplicate headers, including one empty and one nonempty. Existing normal/empty-header tests remain. | Fix staged; exact-head and independent review pending |
| P2 | Package; HTTP intermediary policy, confidentiality | For cached HTTP results on authentication-opt-in routes, generate private, no-store on MISS/HIT/304, including anonymous requests to those routes and returned Response objects. Server-side storage remains governed by the explicit identity-aware builder. | Fix staged; exact-head and independent review pending |
| P3 | Package; explicit Request with default builder and explicit header variations | Preserve read/write bypass, versioned hashed Vary keys, all declared field values and no storage of uncovered Vary/private/no-store on evaluated responses. Regression tests and Redis fixtures. | Verify final artifact; no blanket safety claim |
| P4 | Package; legacy key/namespace migration | Preserve ordinary keys; ensure protected requests do not access previous unsafe entries. Verify selective cleanup, unrelated entries and ordinary-data rollback. | Final artifact proof required |

These changes do not authenticate a request. Reject ambiguous credentials
in the application's authentication layer. HTTP policy on responses for
which the decorator bypasses caching is the application's responsibility.
Changing generated headers cannot purge an intermediary's existing cached
responses; invalidate those caches when migrating affected routes.

## Residual requirements for callers

| ID | Ownership / impact | Required consumer action | Proposed disposition |
|---|---|---|---|
| A1 | Application; hidden context, custom authentication and role/tenant state, confidentiality | Authenticate/authorize before cache lookup. Use validated identity, role, tenant and every representation dimension in a reviewed key, or do not decorate the endpoint. The synthetic hidden-context test characterizes the unsafe configuration and explicit no-cache alternative. | Accept only with documented action and independent review |
| A2 | Application/infrastructure; forwarded identity, Host and proxy trust | Strip untrusted forwarding headers; trust only configured intermediaries; validate host, identity and tenant. Never infer authorization from Vary. | Same |
| A3 | Shared; attacker-controlled cardinality, availability | Normalize/limit header values, request size and rates; use bounded TTLs, memory quotas/eviction and optional local entry cap. Hashing does not authenticate or bound entry count. | Same |
| A4 | Shared; stale/legacy private Redis or intermediary entries, confidentiality | Rotate affected prefixes or perform selective purge before serving; invalidate intermediary caches; do not restore unsafe historical caching on rollback. Never flush unrelated data. | Same; block if protected path reads unsafe data |
| A5 | Package design/application deployment; process-global configuration, isolation | One reviewed configuration per process. Separate processes/backends/prefixes when isolation is required; do not reset or force-reconfigure a live process shared by unrelated apps. App-scoped redesign is future #99. | Same; no claim of per-app isolation |
| A6 | Application/backend trust; deserialization | Do not use PickleCoder with attacker-controlled/untrusted cache bytes, credentials or backend access. | Same |

A private/no-store result or Vary discovered only after executing an
endpoint is not a retroactive invalidation of a previously cached shared
entry; cache hits skip endpoint execution. Dynamic privacy policies must
be evaluated before lookup or the application must bypass caching.
Neither the library nor this risk record guarantees that all hidden
response inputs are detectable.

## Evidence and decision gates

- Source-level regression suites: tests/test_auth_privacy.py,
  tests/test_vary_headers.py, migration Phase B and exact installed security.
- Candidate CI and synthetic fixtures are not third-party adoption.
- The final record must include exact source SHA, both artifact SHA-256
  values, successful run IDs, new/reopened advisory disposition, reviewer
  decision and independent review of the scoped residuals. Historical
  0.5.0 risk acceptance is not consent for 0.6.0.
- Any demonstrable unmitigated package-controlled private replay is
  NO-GO. Fix it instead of labeling it application-owned.
- Reconsider upon new auth/cache behavior, configuration redesign,
  reproduced cross-tenant issue or relevant vulnerability.

**Current decision: pending independent counteraudit and final-artifact
acceptance.** No tag or publication is authorized by this document.


## Contraauditoría de release — 2026-11-21

**Decisión: GO para la política, CONDITIONAL GO para las correcciones
técnicas; NO-GO para fusionar/publicar todavía.** Revisión de fuente
y logs de #104, HEAD `f11aa65fa720024b87a66b33fc72a88ca12c7358`,
base `cf9983ce34e92ea2bb4ad4568a195191305fe914`.
Este anexo registra la revisión de ese SHA; agregarlo cambia el HEAD
y no transfiere automáticamente las conclusiones de CI.
No constituye certificación profesional externa, aprobación del
mantenedor ni evidencia de adopción. No se ejecutó ninguna publicación.

### Evidencia comprobada

- 78/78 jobs exitosos en ocho workflows del HEAD indicado:
  [CI 29/29](https://github.com/agustin18/fastapi-cache/actions/runs/44930760581),
  [Phase B 20/20](https://github.com/agustin18/fastapi-cache/actions/runs/44930760540),
  [Redis 17/17](https://github.com/agustin18/fastapi-cache/actions/runs/44930760552),
  [diagnóstico instalado 7/7](https://github.com/agustin18/fastapi-cache/actions/runs/44930760576),
  CodeQL, docs, changelog y título (5/5).
- Phase B construyó una sola pareja; 12 lanes de migración/rollback
  y siete perfiles de seguridad instalaron su distribución seleccionada.
  Logs de jobs 136926871548 y 136926871565 corroboran descarga del mismo
  bundle, verificación de ambos hashes, y respectivamente probe instalado
  de privacidad/Redis y auditoría del perfil sdist/all.
- Artifact 14717771216, digest ZIP
  `sha256:5362a1fea1b9e0fae20bd7197b4ea3eae99554bdf943ed766742f386b9032ff6`.
  Es el digest del contenedor de GitHub, NO los dos hashes individuales.
  Los logs muestran verificación de los archivos, no recalculé los
  archivos descargados independientemente. Los hashes de #94 no son
  evidencia para #104 ni para el futuro SHA final.
- Tag v0.6.0: consulta GitHub devuelve 404. Los workflows de upload no
  fueron ejecutados; no comprobé permisos/protecciones de entornos
  mediante la API disponible ni una descarga real desde TestPyPI.

### Hallazgos y condiciones

| ID | Severidad | Evidencia y acción |
|---|---|---|
| CA1 | Alta, bloquea merge | README.md y MIGRATION.md publican ejemplos de identity_key_builder con headers.get y concatenación delimitada de datos, seguida de HMAC. La clasificación del decorador ahora observa todas las ocurrencias, pero el ejemplo selecciona solamente una; HMAC no corrige una serialización ambigua. Con Starlette 0.50.0 local y datos sintéticos confirmé igualdad de los digests de dos tuples de cabeceras distintos y de dos solicitudes con ocurrencias distintas de una credencial. Esto demuestra que el ejemplo no es una función de identidad inequívoca, no una explotación de una aplicación real ni una fuga nueva del decorador. Reemplazar ambos ejemplos por construcción explícita, no ambigua, basada en la identidad autenticada y autorizada (incluyendo contexto, ruta, permisos y argumentos pertinentes), rechazar ambigüedad en autenticación; no ofrecer un generador universal. Corregir la anotación Request del ejemplo de MIGRATION. Probar separación y fallo seguro; revisar fixtures opt-in que usan helpers simplificados. |
| CA2 | Media, bloquea aceptación del flujo de promoción | scripts/verify_release_bundle.py verifica repositorio, run, SHA, rama, workflow, conclusión, intento, versión, nombres, manifest y bytes. tests/test_release_bundle.py cubre varias negativas pero no ejecuta verify_test_index ni prueba funcionalmente preflight de tag/checkout y descarga cross-run. Añadir tests con JSON simulado de TestPyPI (exacto, hash diferente, falta/sobra archivo, versión incorrecta, respuesta inválida/error), y prueba no-publicante de preflight/recuperación del bundle de un run válido al preparar el SHA final. No se requiere publicar para probar el rechazo. |
| CA3 | Media, antes de publicar | Los gates confían en el workflow revisado y el éxito del run; comprobar explícitamente los 20 jobs previstos y provenance/run_attempt y hashes de cada lane en el mismo intento. El manifest del sdist corresponde al archivo fuente, no al wheel derivado por pip. Usar un run nuevo entero si se necesita repetir; no reutilizar lanes/artifacts de otro intento. La antigüedad del bundle y las resoluciones transitivas pueden variar: obtener evidencia fresca inmediatamente antes de la promoción, repetir con cambios, y preservar una revisión autenticada Dependabot. Confirmar protecciones efectivas y confianza del tag/entorno. |
| CA4 | Baja / próxima release | Phase B y nombre del artifact tienen versión 0.6.0 fija; verify_release_bundle restringe versiones finales X.Y.Z. No es un flujo RC general ni automáticamente sirve para 0.7.0. El candidato menciona RC solo con aprobación separada: aclarar que requiere adaptación y pruebas, no prometerlo. Parametrizar el próximo tren antes de cambiar versión, sin debilitar hashes/provenance. |
| CA5 | Media, higiene de promoción | README/MIGRATION explican correctamente que la caché interna no configura CDN, pero deben explicar el cambio de HTTP private/no-store de 0.6.0 y purga de intermediarios, conservando versión 0.5.0. Revisar textos absolutos de seguridad/migración y registros históricos con datos identificables sin repetirlos ni alterar tags pasados. No promocionar source candidate como disponible. Towncrier, docs, tests de estado de versión y final ledger deben completarse en el PR de promoción. |

### Política, seguridad y riesgos

GO definitivo para la política permanente de CONTRIBUTING: #91 retirado,
sin cuotas de adopción, deployment, testimonios, hosting ni certificación
externa obligatoria; las pruebas sintéticas, integraciones y pruebas del
mantenedor son evidencia técnica acotada. Los documentos activos examinados
no afirman adopción independiente, superioridad medida ni aislamiento
universal. Conservar registros históricos como tales, no como requisitos
activos; separar difusión de publicación. No existe obligación de
mencionar el número de usuarios en cada nota de versión.

- P1: código inspeccionado usa getlist y any sobre Authorization/Cookie
  no vacíos; incluye valores duplicados, preserva bypass antes del
  backend. Las cabeceras vacías sin valor siguen tratándose como ausencia;
  autenticación debe rechazar credenciales ambiguas. Aprobación de
  alcance condicionada a CA1 y regresiones finales, no aislamiento genérico.
- P2: política generada en MISS/HIT/304 para caching autenticado opt-in,
  también solicitudes anónimas, y copia sobre Response retornada cuando
  corresponde. Suite/fixture instalados verdes; el opt-in requiere
  custom key builder completo y validación previa. Añadir casos de
  JSONResponse con JsonCoder, opt-in global/override y Redis si faltan;
  el código no configura intermediarios ni purga respuestas antiguas.
  Respuestas bypass, errores, retornos no codificables y cabeceras
  posteriores de middleware requieren política de la aplicación.
- P3/P4: bypass con Request explícito/default y Vary declarado,
  golden ordinary keys y rollback verificados en alcance candidato.
  Vary privado no inferido, HIT no ejecuta handler; no usar metadatos
  dinámicos posteriores al lookup como control de acceso.
- A1/A2/A3/A4/A5/A6: se mantienen los límites tabulados: identidad y
  permisos completos y validados, proxies confiables, normalización
  y límites de cardinalidad, purga selectiva, separación de procesos y
  backend confiable para deserialización. El mantenedor puede aceptar
  estos residuales explícitamente con acciones concretas y evidencia de
  sus mitigaciones. No se acepta una fuga controlada por la biblioteca.
  CA1 es documentación propia del paquete, no riesgo que pueda
  transferirse íntegramente al consumidor.

La ausencia de auditor contratado no impide una release: revisar
independientemente cuando sea posible, registrar quién aprobó en su
rol real y limitar las afirmaciones al alcance probado. La decisión
de #53 queda pendiente hasta CA1 y evidencia final. No declarar
que no existen vulnerabilidades.

### Publicación y roadmap

Antes del tag: solventar CA1/CA2, revisar el diff exacto y CI; preparar
y fusionar con autorización la promoción Towncrier; documentación
versionada, metadata y changelog, final stable SHA, run manual Phase B
completo + seguridad/CI, hashes individuales, provenance y delta
Dependabot autenticado; resolver vulnerabilidades nuevas y aceptar
residuales explícitamente. Preservar 0.5.0. Confirmar configuración
de entornos y autorizar el tag anotado de la versión por separado.

TestPyPI: autorizar, ejecutar sobre ese tag y run final de stable con
los dos hashes explícitos; verificar bytes descargados y smoke install.
PyPI: autorización separada, repetir evaluación de seguridad/delta,
verificar igualdad con digests del índice de prueba y mismos archivos
antes de upload; comprobar ambos hashes desde PyPI después. No
reconstruir ni usar artefactos de otro SHA/intento.

Redacción pública (solo cuando sea cierta):
"Version 0.6.0 adds optional bounded InMemory caching and targeted
privacy fixes. Release verification covers the documented runtime matrix,
installed distributions, controlled Redis migration/rollback and dependency
security checks. Application-specific authentication, tenant, permissions
and hidden context require explicit isolation or bypass. Report reproducible
issues via GitHub; report vulnerabilities privately."
No claims production-proven, independently adopted, universally safe,
zero vulnerabilities, guaranteed tenant isolation, fastest, complete
feature parity or universal drop-in compatibility.

Roadmap: 0.7 #100 baseline antes de #50/#96; pruebas de concurrencia,
cancelación, invalidación, privacidad y sobrecoste OFF; #51/#55 en
paralelo según evidencia. 0.8 #97/#98 después de contratos de race/TTL.
0.9 #99 diseño temprano, implementación cuando probada; #49 y
coordinación distribuida después. #102/#103 investigación. No ampliar
0.6. #91 permanece cerrada; #53/#92 abiertas hasta evidencia final;
#48/#88 separadas. No nuevos tickets duplicados: CA1/CA2/CA3 se
resuelven en el release existente; CA4 antes de la siguiente versión.

**Para revertir el NO-GO:** corrección CA1, pruebas de CA2, verificación
CA3, review del diff actualizado y nueva CI verde, aceptación documentada
del mantenedor, promoción final y verificaciones exactas recién descritas.
Esta revisión no autoriza el merge, tag ni publicación.


### Remediation follow-up (pending verification)

CA1: replace the ambiguous raw-header examples with a narrowly scoped
structured HMAC over validated identity dimensions, fail closed for missing
identity and unsupported contexts, and test the documented code.
Synthetic test helpers use all header occurrences; add plain JSONResponse
opt-in regression. CA2: exercise TestPyPI verification with controlled
negative cases; require exact named job matrix and first attempt for both
promotion workflows. CA3: migration lanes check source, run and attempt;
use a new full dispatch rather than mixing reruns. Actual final stable
bundle download/tag preflight, environment settings, security freshness,
maintainer acceptance and publication remain separate final gates.
CA4/CA5: clarify RC scope and candidate HTTP policy in migration guides.
No release authorization; run new HEAD checks and incremental review.
