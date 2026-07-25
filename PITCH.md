# Guion del pitch — 2 minutos

> Objetivo: que el jurado (ingenieros de ReshapeX, expertos en anti-alucinación)
> recuerde **un momento** y se lleve **un número**. No es una lista de features.

Quién maneja el demo y quién narra se decide antes. Nadie improvisa.

---

## Estructura (2:00)

### 1. El problema, con un caso concreto (0:00–0:20)

> "Cuando a alguien se le daña la nevera, no llama al vendedor: abre WhatsApp y
> pregunta. Y ahí es donde un asistente de IA es peligroso — porque si inventa
> un número de repuesto o dice que algo está en garantía cuando no lo está, le
> cuesta plata real a la persona. **Una respuesta equivocada dicha con seguridad
> cuesta más que ninguna respuesta.**"

*(Esa última frase es textual de ReshapeX. Que la reconozcan.)*

### 2. Qué construimos, en una frase (0:20–0:35)

> "Construimos un agente de **ciclo de vida** para Haceb: acompaña el
> electrodoméstico antes de comprarlo —si cabe en la cocina, cuánto gasta de
> luz— y después —fallas, garantía, mantenimiento. Y su diferencial no es lo
> que sabe, es **lo que se niega a inventar**."

### 3. Demo en vivo — el momento que se recuerda (0:35–1:35)

Esta es la parte que gana. **El jurado toca, no nosotros.** Secuencia:

1. **Foto → producto.** Subimos la foto de una placa de datos. El agente lee la
   referencia con visión y la confronta contra el catálogo real. *"Nadie se sabe
   la referencia de memoria; la placa sí está pegada al equipo."*
2. **Una pregunta con dato real.** *"¿Cabe en un hueco de 65 cm y pasa por una
   puerta de 70?"* → el agente responde con las medidas exactas y **la fuente**.
   Se abre el panel: se ven las herramientas que llamó y el sello verde del
   auditor.
3. **El momento clave — que intenten romperlo.** Le decimos al jurado:
   > "Pregúntenle lo que quieran. Intenten hacerlo mentir."

   Y mostramos el caso del repuesto: el agente **se niega** a dar una referencia
   de repuesto porque el catálogo no publica compatibilidad, y **escala a
   servicio técnico** en vez de adivinar. Ahí está la tesis de ReshapeX, en vivo.

### 4. Cómo está construido (1:35–1:55)

> "Por dentro: **RAG sobre una base de datos vectorial** (Chroma) con los
> manuales oficiales, embeddings de Gemini, y búsqueda híbrida. El agente nunca
> responde de memoria: cada dato sale de una herramienta o de un manual, con
> cita. Y un **segundo agente audita** cada respuesta antes de mostrarla — si no
> puede respaldar una afirmación, la marca. Memoria entre turnos, y funciona
> igual en web y en WhatsApp."

*(Nombrar aquí los 5 componentes del checklist: RAG + base vectorial,
herramientas externas, memoria, ingeniería de contexto, sub-agente. Todos
funcionando, no mencionados.)*

### 5. El número (1:55–2:00)

> "Y no solo lo afirmamos, **lo medimos**: corrimos un set de preguntas
> adversariales y el agente tuvo **[X] alucinaciones** — respondió con fuente
> cuando había dato, y rechazó cuando no lo había."

*(Rellenar [X] con el resultado real del `python -m evals.run`. Si es 0, es el
cierre perfecto.)*

---

## Por qué esto le pega a ESTE jurado

ReshapeX vende *"the knowledge grounding layer for industrial AI"* con la promesa
*"99.9% measured pass rate on your own evals"*. Nuestro proyecto es esa misma
idea aplicada a una marca de consumo colombiana:

- **La base vectorial + RAG** es el "grounding layer".
- **El sub-agente validador** es el control de calidad antes de mostrar.
- **El eval con un número** es exactamente su forma de medir.
- **El escalamiento en vez de adivinar** es su "route uncertain answers to
  experts rather than guessing".

No estamos haciendo *un chatbot de catálogo* (el proyecto obvio, que van a ver
varias veces). Estamos haciendo **la capa de confianza para postventa**.

---

## Preguntas del jurado — respuestas listas

**¿Qué pasa si le preguntan algo que no está en los documentos?**
Lo demostramos en vivo: dice que no lo tiene y escala. No rellena el hueco.

**¿De dónde salió ese dato?**
Se abre el panel de confianza: cada respuesta muestra qué herramienta la produjo
y la URL de la fuente.

**¿Qué está mockeado y qué funciona de verdad?**
Nada mockeado. El catálogo es la API pública real de Haceb (47 productos), los
manuales son los PDFs oficiales (17), la base vectorial tiene 746 pasajes. Se
puede abrir el repo y verificarlo.

**¿Por qué Chroma y no solo embeddings en memoria?**
Porque queríamos una base vectorial real, persistente y consultable, no un
arreglo temporal. Y porque combinamos búsqueda semántica con BM25: el usuario
dice "no enfría" y el manual dice "poco frío en el compartimiento inferior" —
sin la parte semántica, no lo encuentra.

**¿Por qué un sub-agente validador y no una regla en el prompt?**
Un modelo que se autoevalúa en el mismo turno tiende a darse la razón. El
auditor es un agente separado, con temperatura 0 y una sola tarea.

---

## Checklist antes de subir a presentar

- [ ] La app corre y responde (probar 1 pregunta 5 min antes).
- [ ] Hay cuota de API disponible — **usar la key con más cuota del equipo**.
- [ ] La foto de la placa está lista para subir.
- [ ] El caso del repuesto está ensayado (es el clímax).
- [ ] El número del eval está actualizado en la diapositiva.
- [ ] Todos saben quién dice qué. El demo no se improvisa.
