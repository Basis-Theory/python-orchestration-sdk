# Processing Payments

This guide explains how to process different types of payments using the Payment Orchestration SDK.

## Table of Contents
- [Customer Initiated Transactions (CIT)](#customer-initiated-transactions)
- [Merchant Initiated Transactions (MIT)](#merchant-initiated-transactions)
- [Card-on-File Payments](#card-on-file-payments)
- [3DS Authentication](#3ds-authentication)
- [Using Token Intents](#using-token-intents)
- [Using Processor Tokens](#using-processor-tokens)

## Customer Initiated Transactions (CIT)

### One-Time Payments

For one-time payments where you don't want to store the card for future use:
```python
transaction_request = TransactionRequest(
    reference='unique-transaction-reference',
    type=RecurringType.ONE_TIME,
    amount=Amount(
        value=1000,
        currency='USD'
    ),
    source=Source( # or 'basis_theory_token_intent'
        type=SourceType.BASIS_THEORY_TOKEN,
        id='YOUR_BASIS_THEORY_TOKEN_ID',
        store_with_provider=False
    ),
    customer=Customer(
        reference='customer-reference'
    )
)

response = await sdk.adyen.transaction(transaction_request)
```

### $0 Authentication

Transact and store a card for future use with a provider (card on file):

```python
transaction_request = TransactionRequest(
    reference='unique-transaction-reference',
    type=RecurringType.CARD_ON_FILE,
    amount=Amount(
        value=0,
        currency='USD'
    ),
    source=Source( # or 'processor_token' or 'basis_theory_token_intent'
        type=SourceType.BASIS_THEORY_TOKEN,
        id='YOUR_BASIS_THEORY_TOKEN_ID',
        store_with_provider=True,
        holder_name='John Doe'
    ),
    customer=Customer(
        reference='customer-reference',
        first_name='John',
        last_name='Doe',
        email='john.doe@example.com',
        address=Address(
            address_line1='123 Main St',
            city='New York',
            state='NY',
            zip='10001',
            country='US'
        )
    )
)

response = await sdk.adyen.transaction(transaction_request)
```

### Card-on-File Payments

Transact and store a card for future use with a provider (card on file):

```python
transaction_request = TransactionRequest(
    reference='unique-transaction-reference',
    type=RecurringType.CARD_ON_FILE,
    amount=Amount(
        value=1000,
        currency='USD'
    ),
    source=Source(  # or 'processor_token' or 'basis_theory_token_intent'
        type=SourceType.BASIS_THEORY_TOKEN,
        id='YOUR_BASIS_THEORY_TOKEN_ID',
        store_with_provider=True,
        holder_name='John Doe'
    ),
    customer=Customer(
        reference='customer-reference',
        first_name='John',
        last_name='Doe',
        email='john.doe@example.com',
        address=Address(
            address_line1='123 Main St',
            city='New York',
            state='NY',
            zip='10001',
            country='US'
        )
    )
)

response = await sdk.adyen.transaction(transaction_request)
```

### First subscription / unscheduled payment

For the first subscription payment when a customer is adding a new card for the first time:
```python
transaction_request = TransactionRequest(
    reference='unique-transaction-reference',
    type=RecurringType.SUBSCRIPTION,  # or RecurringType.UNSCHEDULED
    amount=Amount(
        value=1000,
        currency='USD'
    ),
    source=Source(  # or 'processor_token' or 'basis_theory_token_intent'
        type=SourceType.BASIS_THEORY_TOKEN,
        id='YOUR_BASIS_THEORY_TOKEN_ID',
        store_with_provider=True,
        holder_name='John Doe'
    ),
    customer=Customer(
        reference='customer-reference',
        first_name='John',
        last_name='Doe',
        email='john.doe@example.com',
        address=Address(
            address_line1='123 Main St',
            city='New York',
            state='NY',
            zip='10001',
            country='US'
        )
    )
)

response = await sdk.adyen.transaction(transaction_request)
```

## Merchant Initiated Transactions (MIT)

### Charge with On-file PAN

Charge a card for a subscription payment: 

```python
transaction_request = TransactionRequest(
    reference='unique-transaction-reference',
    type=RecurringType.SUBSCRIPTION,  # or RecurringType.UNSCHEDULED
    merchant_initiated=True,
    amount=Amount(
        value=1000,
        currency='USD'
    ),
    source=Source(  # or 'processor_token' or 'basis_theory_token_intent'
        type=SourceType.BASIS_THEORY_TOKEN,
        id='YOUR_BASIS_THEORY_TOKEN_ID',
        store_with_provider=True,
        holder_name='John Doe'
    ),
    customer=Customer(
        reference='customer-reference'
    )
)

response = await sdk.adyen.transaction(transaction_request)
```

## 3DS Authentication

When using a third party 3DS provider, the values will be sent in the `three_ds` field:

```python
transaction_request = TransactionRequest(
    reference='unique-transaction-reference',
    type=RecurringType.ONE_TIME,
    amount=Amount(
        value=1000,
        currency='USD'
    ),
    source=Source(
        type=SourceType.BASIS_THEORY_TOKEN,
        id='YOUR_BASIS_THEORY_TOKEN_ID',
        store_with_provider=False
    ),
    customer=Customer(
        reference='customer-reference'
    ),
    three_ds=ThreeDS(
        eci='05',
        authentication_value='YOUR_3DS_AUTH_VALUE',
        xid='YOUR_3DS_XID',
        version='2.2.0'
    )
)

response = await sdk.adyen.transaction(transaction_request)
```

## Using Basis Theory Token Intents

When using a Basis Theory token intent, you'll pass in the value of the token intent in the `source` field:

```python
# Then use the token intent in a transaction
transaction_request = TransactionRequest(
    reference='unique-transaction-reference',
    type=RecurringType.ONE_TIME,
    amount=Amount(
        value=1000,
        currency='USD'
    ),
    source=Source(
        type=SourceType.BASIS_THEORY_TOKEN_INTENT,
        id=token_intent_id,
        store_with_provider=False
    ),
    customer=Customer(
        reference='customer-reference'
    )
)

response = await sdk.adyen.transaction(transaction_request)
```

## Using Processor Tokens

Transact with card stored with a processor (processor token):

```python
transaction_request = TransactionRequest(
    reference='unique-transaction-reference',
    type=RecurringType.UNSCHEDULED,
    merchant_initiated=True,
    amount=Amount(
        value=1000,
        currency='USD'
    ),
    source=Source(
        type=SourceType.PROCESSOR_TOKEN,
        id='PREVIOUSLY_STORED_PROCESSOR_TOKEN'
    ),
    customer=Customer(
        reference='customer-reference'
    )
)

response = await sdk.adyen.transaction(transaction_request)
```

## Response Handling

We strongly suggest you store the following fields in your database:

- Basis Theory Token Id
    -  If you haven't already stored this token in your database, you should do so now.
- Processor Token (`source.provisioned.id`)
    - This ID ensures a merchant is capable of charging directly with a processor without dependence on Basis Theory
- Network Transaction Id (`networkTransactionId`)
    - This ID ensures the network (Visa, Mastercard, etc) can correlate a merchant's charges when they utilize a multi-processor strategy.

Find the full response model [here](./api-reference.md#transactionresponse).
