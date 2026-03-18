# Referencias y Fundamentos

> *Loom-Context no se basa en intuición. Cada decisión de diseño tiene fundamento en ingeniería de software, ciencia cognitiva y buenas prácticas documentadas.*

---

## Arquitectura de Software

### Clean Architecture
- **Martin, R. C.** (2017). *Clean Architecture: A Craftsman's Guide to Software Structure and Design*. Prentice Hall.
  - Cap. 22: "The Clean Architecture" — las reglas de dependencia que Loom detecta y enforcea (domain no depende de nada, las capas externas dependen de las internas).
  - Cap. 20: "Business Rules" — por qué `domain/` debe ser puro y sin dependencias de frameworks.

- **Martin, R. C.** (2003). *Agile Software Development: Principles, Patterns, and Practices*. Prentice Hall.
  - Dependency Inversion Principle (DIP): la base teórica de por qué Loom genera `layer_boundaries` con `forbidden_imports`.

### Hexagonal Architecture (Ports & Adapters)
- **Cockburn, A.** (2005). "Hexagonal Architecture." *alistair.cockburn.us/hexagonal-architecture/*
  - El paper original que define ports como contratos y adapters como implementaciones. Loom detecta este patrón buscando `ports/` y `adapters/` en la estructura.

- **Vernon, V.** (2013). *Implementing Domain-Driven Design*. Addison-Wesley.
  - Cap. 4: "Architecture" — combina hexagonal con DDD. Referencia directa para proyectos que usan `domain/entities/` + `domain/ports/`.

### Domain-Driven Design
- **Evans, E.** (2003). *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Addison-Wesley.
  - Cap. 4: "Isolating the Domain" — por qué la capa domain debe estar aislada. Fundamento de las boundary rules de Loom.
  - Cap. 5: "A Model Expressed in Software" — entidades, value objects, repositories como patrones que Loom detecta vía suffixes.

### Design Patterns
- **Gamma, E., Helm, R., Johnson, R., Vlissides, J.** (1994). *Design Patterns: Elements of Reusable Object-Oriented Software*. Addison-Wesley.
  - Strategy Pattern (p. 315): usado internamente por Loom (scanners intercambiables) y detectado en proyectos (archivos `*Strategy.ts`).
  - Facade Pattern (p. 185): `LoomEngine` como facade que simplifica la complejidad.
  - Observer Pattern (p. 293): detectado cuando Loom encuentra directorios `events/` o `bus/`.
  - Template Method (p. 325): `BaseScanner` define el esqueleto, subclases implementan `scan()`.

- **Freeman, E., Robson, E.** (2020). *Head First Design Patterns*, 2nd Edition. O'Reilly.
  - Referencia accesible para los patrones que Loom detecta: Factory, Adapter, Strategy, Observer.

---

## Ciencia Cognitiva y la Analogía del Cerebro

### Memoria de Trabajo
- **Baddeley, A. D., & Hitch, G.** (1974). "Working Memory." In *Psychology of Learning and Motivation*, Vol. 8, pp. 47-89. Academic Press.
  - El modelo de memoria de trabajo de Baddeley: capacidad limitada (~7 items), buffer episódico, ejecutivo central. Loom genera exactamente 7 archivos en `.context/` como analogía funcional de la memoria de trabajo — lo que la IA necesita "tener activo".

- **Cowan, N.** (2001). "The magical number 4 in short-term memory: A reconsideration of mental storage capacity." *Behavioral and Brain Sciences*, 24(1), 87-114.
  - Revisión de Miller (1956): la capacidad real es ~4 chunks, no 7. Loom mitiga esto con `quick_rules` (las reglas más críticas primero) y consumo progresivo.

- **Miller, G. A.** (1956). "The Magical Number Seven, Plus or Minus Two." *Psychological Review*, 63(2), 81-97.
  - El paper clásico sobre límites de la memoria de trabajo. Justifica por qué Loom comprime 700 archivos en 7 documentos de contexto.

### Carga Cognitiva
- **Sweller, J.** (1988). "Cognitive Load During Problem Solving: Effects on Learning." *Cognitive Science*, 12(2), 257-285.
  - Teoría de carga cognitiva: la carga extrínseca (información irrelevante) reduce la capacidad de procesamiento. Loom reduce carga extrínseca al filtrar noise (node_modules, .git, secrets) y presentar solo metadata relevante.

- **Kalyuga, S., & Renkl, A.** (2010). "Expertise reversal effect and its instructional implications." *Instructional Science*, 38(3), 209-215.
  - El efecto de reversión por expertise: información útil para novatos puede ser noise para expertos. El consumo progresivo de Loom (quick_rules → full context) permite que cada agente tome solo lo que necesita.

### Chunking y Compresión de Información
- **Chase, W. G., & Simon, H. A.** (1973). "Perception in Chess." *Cognitive Psychology*, 4(1), 55-81.
  - Los expertos en ajedrez no ven piezas individuales — ven *chunks* (patrones). Loom hace lo mismo: no reporta 700 archivos individuales, reporta patterns ("clean-architecture", "I-prefix interfaces", "Repository suffix").

### Dual Process Theory
- **Kahneman, D.** (2011). *Thinking, Fast and Slow*. Farrar, Straus and Giroux.
  - Sistema 1 (rápido, automático) vs Sistema 2 (lento, deliberativo). `quick_rules` es el Sistema 1 de la IA: reglas inmediatas que no requieren análisis. Los archivos completos son Sistema 2: cuando necesita razonar sobre arquitectura.

---

## Ingeniería de Software y Prácticas

### Naming Conventions
- **Martin, R. C.** (2008). *Clean Code: A Handbook of Agile Software Craftsmanship*. Prentice Hall.
  - Cap. 2: "Meaningful Names" — nombres que revelan intención. Fundamento de por qué Loom detecta y enforcea convenciones de naming.

- **Google TypeScript Style Guide.** *google.github.io/styleguide/tsguide.html*
  - Referencia de industria para PascalCase (clases), camelCase (funciones), UPPER_CASE (constantes). Loom detecta estos estilos automáticamente.

- **Microsoft TypeScript Coding Guidelines.** *github.com/microsoft/TypeScript/wiki/Coding-guidelines*
  - Referencia para el prefijo `I` en interfaces (debatido pero ampliamente usado). Loom lo detecta cuando >60% de interfaces lo usan.

### Software Architecture Documentation
- **Bass, L., Clements, P., & Kazman, R.** (2012). *Software Architecture in Practice*, 3rd Edition. Addison-Wesley.
  - Cap. 18: "Architecture Documentation" — qué debe contener la documentación de arquitectura. `.context/architecture.md` sigue estos principios: vistas, restricciones, decisiones.

- **Brown, S.** (2018). *Software Architecture for Developers*, Vol. 2. Leanpub.
  - El modelo C4 (Context, Container, Component, Code). Loom genera un equivalente simplificado: `index.json` (context), `architecture.md` (container), `directory-map.md` (component), `naming.md` (code conventions).

### Security by Design
- **OWASP.** "Secure Coding Practices - Quick Reference Guide." *owasp.org/www-project-secure-coding-practices-quick-reference-guide/*
  - Principio de mínimo privilegio: Loom nunca expone contenido de archivos, solo metadata. Nunca incluye secrets.

- **Saltzer, J. H., & Schroeder, M. D.** (1975). "The Protection of Information in Computer Systems." *Proceedings of the IEEE*, 63(9), 1278-1308.
  - Principio de fail-safe defaults: Loom excluye por defecto (hardcoded secrets), el usuario debe opt-in para incluir.

### AI-Assisted Software Engineering
- **Fan, A., et al.** (2023). "Large Language Models for Software Engineering: A Systematic Literature Review." *ACM Transactions on Software Engineering and Methodology*.
  - Revisión sistemática de LLMs en ingeniería de software. Identifica que el contexto del proyecto es el factor #1 para calidad de generación de código.

- **Vaithilingam, P., Zhang, T., & Glassman, E. L.** (2022). "Expectation vs. Experience: Evaluating the Usability of Code Generation Tools Powered by Large Language Models." *CHI Conference on Human Factors in Computing Systems*.
  - Estudio de usabilidad: los desarrolladores reportan que la falta de contexto del proyecto es la principal causa de sugerencias incorrectas de IA. Loom aborda este problema directamente.

- **Barke, S., James, M. B., & Polikarpova, N.** (2023). "Grounded Copilot: How Programmers Interact with Code-Generating Models." *OOPSLA*.
  - Los programadores usan IA en modo "aceleración" (contexto claro) vs "exploración" (contexto ambiguo). Loom maximiza el modo aceleración proveyendo contexto completo.

---

## Analogías y Modelos Mentales

### Redes Neuronales como Modelo
- **McCulloch, W. S., & Pitts, W.** (1943). "A Logical Calculus of the Ideas Immanent in Nervous Activity." *Bulletin of Mathematical Biophysics*, 5, 115-133.
  - El paper fundacional de redes neuronales artificiales. La analogía de Loom con capas del cerebro se inspira en la idea de que la información se transforma al pasar por capas sucesivas (input → hidden → output = scanners → engine → generators).

- **Rumelhart, D. E., Hinton, G. E., & Williams, R. J.** (1986). "Learning representations by back-propagating errors." *Nature*, 323, 533-536.
  - Backpropagation: el feedback loop fundamental. En Loom, el ciclo `scan → generate → audit → fix → rescan` es análogo al backpropagation: las violaciones detectadas informan correcciones que mejoran el siguiente scan.

### Barrera Hematoencefálica
- **Abbott, N. J., Patabendige, A. A., Dolman, D. E., Yusof, S. R., & Begley, D. J.** (2010). "Structure and function of the blood-brain barrier." *Neurobiology of Disease*, 37(1), 13-25.
  - La barrera hematoencefálica protege al cerebro filtrando selectivamente qué sustancias pasan. Loom's `FileFilter` opera bajo el mismo principio: protege al contexto de "toxinas" (secrets, noise) mientras permite "nutrientes" (metadata útil).

---

## Estándares y Convenciones

### Conventional Commits
- **conventionalcommits.org** — Especificación para mensajes de commit estructurados (`feat:`, `fix:`, `docs:`). Loom recomienda y planea detectar este patrón.

### Semantic Versioning
- **semver.org** — Loom sigue SemVer. v0.1.0 = primera release funcional (0.x = API puede cambiar).

### The Twelve-Factor App
- **12factor.net** — Factor III (Config): almacenar config en el environment, no en código. Fundamento de por qué Loom excluye `.env` siempre.

### PEP 8 / PEP 517 / PEP 621
- **python.org/dev/peps/** — Loom sigue PEP 8 para estilo Python, PEP 517 para build system (hatchling), PEP 621 para metadata en pyproject.toml.

---

## Cómo Citar Loom-Context

```bibtex
@software{loom_context,
  author = {Ruiz C., J. Adrian},
  title = {Loom-Context: Architecture Context Engine for AI-First Engineering},
  year = {2026},
  url = {https://github.com/jadruiz/Loom-Context},
  license = {Apache-2.0}
}
```

---

*[Volver al índice →](./INDEX.md)*
