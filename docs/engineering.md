# Engineering notes — Warehouse Manager

Warehouse Manager is a 2021 Java Swing / MySQL desktop project. This document describes the code as it actually exists and the architectural lessons that are visible in it today.

The goal is not to rewrite history by calling it MVC, Clean Architecture, or a production WMS. It is a small desktop system where Swing screens talk directly to a relational database and share state through static fields.

## 1. Original architecture

```text
Swing JFrame / JInternalFrame
        │
        ├── input validation
        ├── navigation
        ├── business calculations
        ├── JDBC queries/updates
        ├── table/chart rendering
        └── email verification
                 │
                 ▼
               MySQL
```

The app contains no separate persistence or service layer. UI classes own the complete request/response loop.

## 2. Main screens

The source tree contains these main classes:

```text
CW2T1           application entry point
SorL            sign-in / registration choice and login flow
SignIn          account registration details
SignIn2         warehouse/package requirement selection
MailVerification registration verification email/code
Interface1      authenticated navigation shell
dashboard       capacity summary + JFreeChart pie chart
moving          transfer/movement workflow
adding          add crates / stock
settings        account/settings operations
passrec         password recovery flow
```

The `.form` files beside many classes are NetBeans GUI Builder metadata.

## 3. Shared state

Several screens communicate through public/static fields rather than passing typed objects.

Examples include registration fields and the authenticated user's warehouse identity.

Conceptually:

```text
SignIn static fields
      │
      ▼
SignIn2 static fields
      │
      ▼
MailVerification
      │
      ▼
registration INSERT
```

and after login:

```text
SorL.username
     │
     ▼
Interface1.getkey()
     │
     ▼
Interface1.keynic
     │
     ├── dashboard
     ├── moving
     ├── adding
     └── settings
```

This makes the flow easy to build quickly, but creates hidden dependencies between screens.

A modern version would use an explicit session/user context object and pass dependencies through constructors or a controller/view-model layer.

## 4. Warehouse capacity model

The project models three crate sizes and derives occupied capacity from them.

The dashboard formula is roughly:

```text
used = large + medium/2 + small/4
free = 100 - used
```

The add/move flows use the same idea when checking whether a request fits the package capacity.

This rule should be a domain function rather than duplicated UI arithmetic.

A testable version would look conceptually like:

```text
capacityUsed(large, medium, small)
canFit(packageCapacity, current, incoming)
```

with unit tests around boundary values.

## 5. Dashboard

`dashboard` reads the current `warehouse_req` row, extracts crate counts and builds a JFreeChart pie dataset.

The chart contains:

```text
free space
large crates
medium crates
small crates
```

This is a useful early example of a UI projection: relational values are transformed into a visualization instead of being shown only as a table.

The original class also referenced a developer-machine absolute image path. The cleanup changes that reference to the bundled classpath image so another machine does not depend on a local `Downloads` directory.

## 6. Moving inventory

The movement screen combines:

```text
source stock
available branches
transport method
requested crate quantities
movement record
```

The UI lets a user inspect their current warehouse data, inspect other branch options, choose a destination and select a Van or Truck.

The current implementation performs the reads and mutations directly inside event handlers.

The important missing abstraction is a transfer transaction.

A safer model is:

```text
BEGIN
  validate source has enough stock
  decrement source stock
  create movement/transfer record
COMMIT
```

If any step fails, the whole operation should roll back.

Without that boundary, partial updates can make stock and movement history disagree.

## 7. Adding stock

The `adding` screen reads current crate counts, validates input and updates the warehouse allocation.

It calculates the final capacity before sending an SQL `UPDATE`.

Again, the rule belongs in a domain service, while the SQL belongs in a repository.

```text
UI
 │ requested quantities
 ▼
InventoryService
 │ validate capacity
 ▼
WarehouseRepository
 │ atomic update
 ▼
MySQL
```

## 8. JDBC configuration

The historical code repeated JDBC configuration in many methods.

The portfolio cleanup centralizes those values through `AppConfig`:

```text
WMS_DB_URL
WMS_DB_USER
WMS_DB_PASSWORD
```

with equivalent JVM system properties available.

The URL/user have local-development defaults. The password deliberately defaults to empty rather than preserving a credential in source.

This is a configuration cleanup, not a claim that environment variables make a desktop client a secure place for production database credentials. A desktop client that connects directly to a privileged database is still the wrong trust boundary for a real system.

## 9. Raw SQL and injection risk

Much of the original code constructs SQL with string concatenation:

```text
"... WHERE nic = '" + value + "'"
```

or builds `INSERT`/`UPDATE` statements directly from Swing fields.

That creates correctness and injection risks.

The right fix is not a regex escape helper. It is parameterized SQL:

```java
PreparedStatement statement = connection.prepareStatement(
    "SELECT * FROM warehouse_req WHERE nic = ?"
);
statement.setString(1, nic);
```

and repository methods that hide SQL from the UI.

I did not mechanically rewrite every generated Swing class into a new persistence architecture because that would turn this historical project into a different application. The README/docs make the limitation explicit.

## 10. Password handling

The historical registration flow writes the password field into the database model as a normal string and authentication is built around direct credential matching.

A current system should use:

```text
password
   │
   ▼
strong password hash (Argon2id / bcrypt / scrypt)
   │
   ▼
stored hash
```

Authentication compares a supplied password against the stored hash; plaintext passwords should not be queryable data.

A desktop app also should not talk directly to the account database. Account authentication belongs behind a server/API boundary.

## 11. Email verification

The original `MailVerification` class sends mail directly from the desktop application through SMTP.

That requires an SMTP credential to be available to every shipped client, which means it cannot be treated as a real secret.

The cleanup removes the literal SMTP credential from current source and reads optional configuration through:

```text
WMS_SMTP_USER
WMS_SMTP_PASSWORD
```

The verification code is also normalized to a six-digit positive value rather than an unrestricted signed integer.

For a real product the better architecture is:

```text
desktop app
    │ request verification
    ▼
backend
    │ owns mail-provider credential
    ▼
email provider
```

The backend should store only a short-lived hashed verification challenge and enforce expiry/attempt limits.

## 12. Threading

JDBC and SMTP work is performed synchronously from Swing flows.

Swing uses the Event Dispatch Thread for UI work. Long database/network calls on that thread can freeze the interface.

A modern desktop version should perform I/O away from the UI thread and publish state back safely.

```text
button click
    │
    ▼
background task / service
    │
    ▼
I/O
    │
    ▼
EDT state update
```

## 13. Connection lifecycle

The original classes repeatedly do:

```text
Class.forName(driver)
DriverManager.getConnection(...)
create Statement
execute
close Statement
close Connection
```

Modern JDBC code should prefer try-with-resources:

```java
try (Connection connection = dataSource.getConnection();
     PreparedStatement statement = connection.prepareStatement(sql)) {
    ...
}
```

For an application making repeated requests, a `DataSource` / connection pool is also a cleaner boundary than `DriverManager` calls in every event handler.

## 14. Database ownership

Observed tables referenced by source include:

```text
registration
warehouse_req
other_branches
moving
```

The database is the single shared persistence layer for account data, warehouse allocation and movement records.

A current schema would benefit from explicit foreign keys, generated IDs, timestamps and transactional constraints rather than relying on UI flow to preserve relationships.

## 15. Branch data

The UI exposes branch/location choices such as Kandy, Colombo, Matara and Jaffna, while dashboard copy also lists Galle.

That illustrates another early design smell: operational reference data is embedded in UI controls/text.

Branch metadata should live in the database or a configuration/service layer and the UI should render the current list.

## 16. NetBeans project structure

This project predates my preference for conventional dependency tooling.

The build is a NetBeans Ant project:

```text
build.xml
manifest.mf
nbproject/
lib/*.jar
```

The repository originally tracked:

```text
build/
dist/
nbproject/private/
```

Those are generated/machine-local artifacts and are removed from the portfolio branch.

The older JAR files under `lib/` remain because they are part of how the historical Ant project resolves its dependencies.

## 17. Binary dependency trade-off

Keeping JARs in Git is not how I would start a current Java project.

Today I would use Maven or Gradle with declared versions and reproducible dependency resolution.

For this repo there are two competing goals:

```text
historical reproducibility
vs
modern repository hygiene
```

I chose to remove generated build artifacts while keeping the libraries the old build definition expects.

## 18. Repository security cleanup

The current-tree cleanup focuses on secrets/configuration and generated artifacts:

- database config routed through `AppConfig`
- SMTP config routed through `AppConfig`
- six-digit verification code generation
- absolute developer image path replaced by classpath resource
- `build/` removed
- `dist/` removed
- `nbproject/private/` removed
- `.gitignore` added

Historical commits still contain the old source values. Any credential that ever existed there should be considered exposed and rotated.

## 19. Testing gap

The historical project has no automated test suite.

The easiest high-value tests to add first would target pure domain rules rather than Swing:

```text
crate capacity calculation
package capacity limits
movement quantity validation
verification-code format
```

Then repository integration tests could use a disposable database/container instead of a developer MySQL instance.

## 20. Rebuild architecture

A modern version could still be a desktop application, but the responsibilities should be split:

```text
Desktop UI
    │
    ▼
ViewModel / controller
    │
    ▼
Domain services
  ├── AccountService
  ├── InventoryService
  └── TransferService
    │
    ▼
API client
    │
    ▼
Backend
  ├── auth
  ├── warehouse repository
  ├── transfer transactions
  └── email provider
    │
    ▼
relational database
```

The desktop client gets user-scoped APIs rather than database credentials.

## 21. Transfer invariants

A warehouse movement feature should make invariants explicit:

```text
quantity >= 0
source has requested quantity
source != destination
movement record and stock mutation are atomic
capacity at destination is respected
```

These rules should be enforced both in domain code and by appropriate database constraints/transactions where possible.

## 22. Why this repository still matters

The code is not valuable because Swing/JDBC event handlers are an architecture to copy.

It is useful because it shows the full learning loop:

```text
UI
-> validation
-> SQL
-> relational state
-> visual dashboard
-> external email
```

and it makes the next engineering step obvious: boundaries, transactions, configuration, testing and trust separation.

That progression is the reason this project belongs in the deeper part of the portfolio rather than being hidden or presented as something newer than it is.
