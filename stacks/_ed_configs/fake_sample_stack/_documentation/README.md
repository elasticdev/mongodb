**Description**

  - This is fake sample stack

**Required**

| argument      | description                            | var type | default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| first_name   | first name                 | string   | None         |
| last_name   | last name                 | string   | None         |
| city        | city of origin          | string    | boston       |

**Optional**

| argument      | description                            | var type | default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| parents       | parents of origin          | dict    | None       |

**Sample entry:**

```
report:
  fake_sample_name:
    dependencies: 
      - infrastructure::dockerhost
    stack_name: elasticdev:::faake_sample_stack
    arguments:
      first_name: bob
      last_name: smith
      city: memphis

```
