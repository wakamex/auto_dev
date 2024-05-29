#
# To scaffold an entirely running agent service from a mermaid spec.

# Current issue
# Scaffold from fsm Spec
autonomy scaffold fsm cex_data_retrieval --spec ../specs/abci/check_cex_balances.yaml
cp ../specs/abci/check_cex_balances.yaml skills eightballer/cex_data_retrieval

# ideally we then perform the overrides


# aea config overrides

```
aea config set vendor.valory.connections.abci.config.target_skill_id eightballer/cex_data_retrieval:0.1.0
aea config set vendor.valory.connections.abci.config.host \${str:localhost}
aea config set vendor.valory.connections.abci.config.port \${int:26658}
aea config set vendor.valory.connections.abci.config.use_tendermint: \${bool:false}
```

```
---
public_id: valory/abci:0.1.0:bafybeihofnsokowicviac6yz3uhur52l3mf54s2hz4i2je5ie4vlruouga
type: connection
config:
  host: ${str:localhost}
  port: ${int:26658}
  target_skill_id: eightballer/cex_data_retrieval:0.1.0
  use_tendermint: ${bool:false }

```

# note these will have to done by appending to the aea config. We first have to check if there is any existing overrides.

# possible for manual override.
```
aea config set vendor.valory.connections.ipfs.config.ipfs_domain /dns/registry.autonolas.tech/tcp/443/https
```

# Abci overrides.

must ensure that use termination is set as so;

this must be set so that use termination is true.
```

      use_termination: true

```
      

```
aea config set skills.rysk_data_retrieval.models.params.args.use_termination false
```


The agent will now run.

However, it will quickly die due to not implemented error.


After fixing the not implemented errors by inheriting from one of the rounds;
```
        setup:
          consensus_threshold: 1
          safe_contract_address: '0x0000000000000000000000000000000000000000'
          all_participants:
          - ${MAS_ADDRESS:str}
```

ensure the agent config has this added to the abci app

# Payloads

Ensure you update the payloads. 

Here we define the data types.

# Rounds

Note we must include at a minum a registration round



```
class FetchCexBalancesRound(CollectSameUntilThresholdRound):
    """FetchCexBalancesRound"""

    payload_class = FetchCexBalancesPayload
    payload_attribute = "cex_balances"
    synchronized_data_class = SynchronizedData

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        if not self.threshold_reached:
            return None
        synchronized_data = self.synchronized_data
        return synchronized_data, Event.DONE


        
```
WARNING: must also set the db post and pre conditions as so;
```

class CexDataRetrievalAbciApp(AbciApp[Event]):
    """CexDataRetrievalAbciApp"""

    initial_round_cls: AppState = FetchCexMarketsRound
    initial_states: Set[AppState] = {FetchCexMarketsRound}
    transition_function: AbciAppTransitionFunction = {
        FetchCexBalancesRound: {
            Event.DONE: FetchCexPositionsRound,
            Event.FAILED: FailedCexRound,
        },
        FetchCexMarketsRound: {
            Event.DONE: FetchCexTickersRound,
            Event.FAILED: FailedCexRound,
        },
        FetchCexTickersRound: {
            Event.DONE: FetchCexBalancesRound,
            Event.FAILED: FailedCexRound,
        },
        FetchCexOrdersRound: {
            Event.DONE: RetrievedCexDataRound,
            Event.FAILED: FailedCexRound,
        },
        FetchCexPositionsRound: {
            Event.DONE: FetchCexOrdersRound,
            Event.FAILED: FailedCexRound,
        },
        RetrievedCexDataRound: {},
        FailedCexRound: {},
    }
    final_states: Set[AppState] = {RetrievedCexDataRound, FailedCexRound}
    event_to_timeout: EventToTimeout = {}
    cross_period_persisted_keys: Set[str] = []
    db_pre_conditions: Dict[AppState, Set[str]] = {
        FetchCexMarketsRound: set({}),
    }
    db_post_conditions: Dict[AppState, Set[str]] = {
        RetrievedCexDataRound: {
            "cex_balances",
            "cex_markets",
            "cex_orders",
            "cex_positions",
            "cex_tickers",
        },
        FailedCexRound: set({}),
    }
```
# Chaining Apps


