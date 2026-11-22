# A negative sample must differ in the field the rule keys on

**Correction.** The first `ag002_negative` sample kept `user: admin` and only
changed the message to "Accepted publickey for backup". Rule AG-002 keys on
`user.name == admin` and a message containing "accepted", so the "negative"
sample matched and `test_rule_ag002_positive_and_negative` failed.

**Rule.** For each rule, write the negative sample by changing exactly one of
the fields the rule tests, so the pair proves that condition matters. Name
which field changed when adding a sample.
