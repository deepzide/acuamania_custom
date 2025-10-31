# For Developers

The only files that you need to init change is `apps.json` and `custom.txt`.

## Tree
```
├── .github // No tocar
├── ansible // No tocar
├── apps.json
├── customer_poc // Custom app 
├── custom.txt // agregar nombre de custom app
├── pyproject.toml 

```

## Configuration Files

### [`apps.json`](apps.json)
Defines the applications to be installed with their repositories and branches.

**Example:**
```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-15",
    "commit_hash": "7ec6ef3139fbc85e8dc2ddfea97dfa87dc84a95e", <- COMMIT HASH
    "version": "15.84.0" <- VERSION
  },
  {
    "url": "https://github.com/frappe/hrms",
    "branch": "version-15",
    "commit_hash": "15a147224465681bfdddcb33c0017aab623cde54", <- COMMIT HASH
    "version": "15.52.0" <- VERSION
  },
  {
    "url": "https://github.com/deepzide/customer_poc",
    "branch": "main"
  }
]
```

### Cómo saber el commit hash
1. Entrar al repo oficial en GitHub.  
2. En los commits, busca el hash como se muestra en la siguiente imagen:  
   ![alt text](hash.png)

---

### [`custom.txt`](custom.txt)
ADD custom applications to be installed (one per line).

**Example:**
```
erpnext
<DEV_CUSTOM>
```

**Important:**  
When adding custom development, both configuration files must be updated:  
- Add the repository URL and branch to [`apps.json`](apps.json)  
- Add the application name to [`custom.txt`](custom.txt)

---

### Próximos Pasos
- [ ] **Agregar DNS**  
- [ ] **Escoger una versión fija de Frappe.** Cuando se actualiza a un release grande, se reinicia el proceso de setup.  
- [ ] **Prueba de Custom App**  
- [ ] **Inicio de Proyecto Cliente**  
- [ ] **Definir rama de production**  
- [ ] **Realizar Snapshot de la instancia en producción antes de hacer un cambio**  
- [ ] **Hacer script de backup de la base de datos hacia un bucket S3 (AWS) para mayor seguridad**  
- [ ] **Prueba de Disaster recovery**  
- [ ] **Agregar DNS a cada IP**  
- [ ] **Buscar manera de que los developers puedan ver los logs (++ pipeline)**  
- [ ] **Disminuir tiempo del pipeline**

---

### Reglas de Operación
Para mantener la estabilidad y seguridad del entorno de producción:

- **Horario Laboral:** No modificar producción en horario laboral.  
- **Backup Obligatorio:** Tomar backup completo de la instancia antes de realizar cualquier cambio en producción.  
- **Ventana de Mantenimiento:** Los cambios en producción deben realizarse fuera del horario laboral o durante ventanas de mantenimiento programadas.

