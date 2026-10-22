---
description: Sincronizar el repo con la Pi por rsync y anotar el commit en ~/keepon/.commit
---

Sincronizá este repo con la Pi (`r2d2@100.116.96.71:keepon/`), en español. Seguí los pasos en orden y frená si uno
falla.

1. **Raíz del repo.** Trabajá desde `git rev-parse --show-toplevel` (la ruta tiene un espacio al final: siempre entre
   comillas).
2. **Estado de git.** Corré `git status --short`. Si hay cambios sin commitear, avisá que la Pi va a recibir archivos
   que no coinciden con ningún commit y preguntá si seguir. Si se sigue, el hash se anota con el sufijo `-sucio`.
3. **Pi accesible.** `ssh -o ConnectTimeout=10 -o BatchMode=yes r2d2@100.116.96.71 true`. Si falla, frená.
4. **rsync** (el de `docs/PI.md`, **sin `--delete`**: no se borra nada en la Pi):
   ```bash
   rsync -a --exclude .venv --exclude .git --exclude logs --exclude __pycache__ --exclude models/ --exclude config.local.yaml ./ r2d2@100.116.96.71:keepon/
   ```
5. **Anotar el commit**, solo si el rsync terminó bien:
   ```bash
   h=$(git rev-parse HEAD); [ -n "$(git status --porcelain)" ] && h="$h-sucio"
   echo "$h" | ssh -o BatchMode=yes r2d2@100.116.96.71 'cat > ~/keepon/.commit'
   ```
6. **Comprobar.** `ssh r2d2@100.116.96.71 cat ~/keepon/.commit` debe coincidir con el hash del paso 5.

Al final, respondé en 2-3 líneas: hash anotado, si hubo cambios sin commitear y un recordatorio de que el rsync no
borra: los archivos que se borraron o renombraron en el repo siguen en la Pi y hay que borrarlos a mano, después de
comparar con `cmp` (regla del `CLAUDE.md`).
