# Warehouse Manager 📦

> a 2021 Java Swing desktop experiment for warehouse space, crate movements, branches and account flows — very much built before I learned to stop putting half the app inside event handlers.

This project started as a coursework-era warehouse management system built with **Java Swing**, **MySQL**, **NetBeans GUI Builder**, **JFreeChart** and **JavaMail**.

It is not presented here as a modern warehouse product. I keep it public because it captures a useful stage in my development: desktop UI state, relational data, registration/login flows, inventory movement, charting, email verification and the architectural mistakes that become obvious once an application grows past a few screens.

`Java` · `Swing` · `MySQL` · `JDBC` · `JFreeChart` · `JavaMail` · `Ant / NetBeans`

## what the original app tried to solve

The application models a small warehouse network where a client can:

- register an account and enter warehouse requirements
- sign in and recover/change account information
- view allocated large / medium / small crate capacity
- see a dashboard pie chart for used vs free warehouse space
- inspect current stock
- inspect available warehouse branches
- choose a branch and transport method for moving crates
- add stock / crate allocations
- keep transfer records
- update profile/settings information
- receive an email verification code during registration

The UI is a set of Swing frames and internal frames generated largely through NetBeans' GUI builder.

## app shape

```text
CW2T1 / entry point
      │
      ▼
   SorL
(sign in / register)
      │
      ├── SignIn
      │     └── account details
      │
      ├── SignIn2
      │     └── warehouse/package requirements
      │
      ├── MailVerification
      │     └── registration confirmation
      │
      ▼
 Interface1
      │
      ├── dashboard
      ├── moving
      ├── adding
      └── settings
             │
             ▼
           MySQL
```

`Interface1` works as the main navigation shell, swapping internal frames into the content area for dashboard, movement, adding and settings screens.

## the dashboard

The dashboard reads the current user's warehouse allocation and turns it into a JFreeChart pie chart.

The original capacity model uses three crate sizes:

```text
large crate   = 1 capacity unit
medium crate  = 1/2 capacity unit
small crate   = 1/4 capacity unit
```

with the remaining percentage displayed as free space.

That is a simple model, but it gave the project a useful exercise in turning relational data into a visual summary instead of showing only tables and text fields.

## moving inventory

The movement screen combines several pieces of state:

```text
current warehouse allocation
        │
        ├── large crates
        ├── medium crates
        └── small crates
        │
        ▼
choose destination branch
        │
        ▼
choose Van / Truck
        │
        ▼
enter crate quantities
        │
        ▼
validate available stock
        │
        ▼
record movement + update warehouse allocation
```

The implementation is very direct: Swing event handlers query MySQL, populate tables and execute updates themselves.

That is exactly the part I would structure differently today.

## data access: useful lesson, bad boundary

The historical code opens JDBC connections directly from UI classes and builds SQL inside event handlers.

A lot of the project effectively follows this shape:

```text
button click
    │
    ▼
construct SQL
    │
    ▼
open MySQL connection
    │
    ▼
read / mutate rows
    │
    ▼
update Swing component
```

That worked for learning the complete loop, but it produces predictable problems:

- duplicated connection configuration
- SQL mixed into presentation code
- difficult testing
- difficult transactions
- raw string-built SQL
- weak separation between domain rules and UI events
- database credentials historically embedded in the client

A modern rebuild should put persistence behind repositories/services and use prepared statements or an ORM rather than concatenated SQL.

## historical security notes

This repository originally contained two classes of credentials directly in desktop source:

1. local MySQL connection credentials repeated across multiple screens
2. SMTP credentials used by the registration-email flow

Those are examples of something a desktop client should not own as secrets.

Even when a value is intended only for a local database, putting credentials in source makes configuration non-portable. SMTP credentials are more serious because anything shipped inside a desktop application can be extracted by the user running it.

The detailed engineering notes explain the safer design I would use now.

> If the historical SMTP account or database credential is still active anywhere, rotate it. Old Git commits remain accessible even after current source is cleaned or configuration is changed.

## repository cleanup

The original repository committed a full NetBeans working directory including generated `build/` output, packaged `dist/` artifacts and private IDE metadata.

Those files are not source, so the portfolio version removes them and keeps the source/build definition instead.

The repository still includes the old local JAR dependencies under `lib/` because this is an Ant/NetBeans-era project. I did not pretend a 2021 Swing coursework app started life with a modern Gradle/Maven dependency graph.

## project shape

```text
warehouse-manager/
├── build.xml
├── manifest.mf
├── lib/
│   ├── javax.mail.jar
│   ├── jfreechart-1.0.19.jar
│   ├── jcommon-1.0.23.jar
│   └── mysql-connector-java-5.1.49-bin.jar
├── nbproject/
│   ├── project.xml
│   └── project.properties
├── src/cw2/t1/
│   ├── CW2T1.java
│   ├── SorL.java / .form
│   ├── SignIn.java / .form
│   ├── SignIn2.java / .form
│   ├── MailVerification.java / .form
│   ├── Interface1.java / .form
│   ├── dashboard.java / .form
│   ├── moving.java / .form
│   ├── adding.java / .form
│   ├── settings.java / .form
│   └── image assets
└── docs/
    └── engineering.md
```

The `.form` files are NetBeans GUI Builder metadata paired with the Swing classes.

## running the historical project

This project was built around a local MySQL database named `wms` and the NetBeans Ant project files in this repository.

To reproduce it faithfully you need:

1. a compatible JDK / NetBeans setup for the old Swing project
2. MySQL running locally
3. the expected WMS schema/tables
4. database configuration adapted to your local machine
5. optional SMTP configuration if testing the historical email-verification path

I do **not** recommend pointing the historical source at a production database or real SMTP credentials.

The project predates containerized local environments and automated migrations, so there is no one-command setup today.

## what aged badly

The main issues are architectural rather than visual:

```text
Swing UI
  + SQL
  + credentials
  + email delivery
  + business rules
all living in the same classes
```

The project also uses:

- plaintext-era account handling
- raw JDBC statements in many places
- globally shared static state between screens
- synchronous database/network operations on UI event flows
- direct SMTP from a client application
- NetBeans-generated classes that became very large
- old pinned binary dependencies

Those are not things I would copy into a current product.

## if i rebuilt it today

For the same desktop-product idea, I would separate it roughly like this:

```text
Swing / JavaFX / Compose Desktop UI
            │
            ▼
      view-model / controller
            │
            ▼
        domain services
       ┌────┴─────────┐
       ▼              ▼
 inventory repo    account service
       │              │
       ▼              ▼
   database       backend/API
```

Specific changes:

- parameterized SQL or JPA/JOOQ instead of string concatenation
- connection pooling/configuration outside source
- hashed passwords
- no SMTP secret in the desktop client
- transactional stock movement
- typed movement/capacity models
- database migrations
- automated tests around crate-capacity rules
- asynchronous I/O so the UI thread stays responsive

I would also treat movement as a transaction: decrement source stock and create the transfer record together, so one cannot succeed without the other.

## why keep this public?

Because it shows something the cleaner recent projects do not: where the architectural instincts came from.

This repo is a snapshot of learning how UI, SQL, charts, email and state all connect. The value now is being able to point at the coupling and explain exactly how I would untangle it.

More detail: [`docs/engineering.md`](docs/engineering.md)
