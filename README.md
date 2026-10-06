# Enterprise Text-to-SQL

## Demarrage avec Docker

Docker Desktop doit utiliser les conteneurs Linux.
Si `app/.env` n'existe pas, copier `app/.env.example` vers `app/.env`
et renseigner `OPENROUTER_API_KEY`.

```powershell
docker compose up -d --build --wait
```

API : http://localhost:8000
Documentation interactive : http://localhost:8000/docs
Etat de la base : http://localhost:8000/health

L'API utilise Python 3.11 sous Linux et conserve LangGraph. Les dependances,
dont orjson, sont installees dans l'image, independamment du `.venv` Windows.
Le fichier `app/.env` est charge au demarrage du conteneur et exclu de l'image.
Compose configure l'adresse PostgreSQL avec le nom du service `postgres`
et utilise le compte `text2sql_reader` defini dans `database/init.sql`.
Le prefixe `postgresql+psycopg2://` selectionne explicitement le pilote
`psycopg2-binary` installe par le projet.

```powershell
docker compose logs --tail 100 api
docker compose exec api python -c "import orjson; from langgraph.graph import StateGraph; print(orjson.__version__)"
docker compose exec api python -m evaluation.evaluators.run_benchmark
```

Pour le benchmark HTTP qui teste `/query`, executer egalement le script
dans le conteneur Linux : il utilise PostgreSQL pour comparer les resultats
des requetes generees et des requetes de reference.

```powershell
docker compose up -d --build --wait
docker compose exec api python -m evaluation.run_api_benchmark
```

La reconstruction inclut les nouveaux fichiers de `evaluation/` dans l'image.
Dans le conteneur de l'API, `http://127.0.0.1:8000/query` pointe vers FastAPI.
Sous Windows, la commande suivante delegue automatiquement le benchmark au
service Docker `api` deja demarre :

```powershell
python -m evaluation.run_api_benchmark
```

Le benchmark compare uniquement les requetes validees et executees sans erreur
par l'agent. Les erreurs HTTP, reseau ou JSON sont enregistrees comme des echecs
sans interrompre les autres exemples.

Le benchmark appelle OpenRouter et peut consommer des credits.
Il enregistre ses resultats dans `/app/evaluation/current_results.json` dans
le conteneur. Pour les comparer a la reference :

```powershell
docker compose exec api python -m evaluation.regression
```

La reference initiale est le benchmark de 8 cas : precision et validation
SQL de 100 %, latence moyenne de 2,06 s et aucune correction.
La commande de regression ne fait aucun appel a OpenRouter.
Pour conserver les resultats sur Windows avant de reconstruire le conteneur :

```powershell
docker compose cp api:/app/evaluation/current_results.json ./evaluation/current_results.json
```

Apres une modification du code ou des dependances, relancer la commande de
demarrage avec `--build`.

Pour arreter les services en conservant les donnees PostgreSQL :

```powershell
docker compose down
```
