# Setup

```sh
git clone https://github.com/efurtak/past_due.git
cd past_due/past_due_app/
make prod_up
```

# Go to URL

<http://localhost/invoices/>

# RabbitMQ management access

<http://localhost:15672/>

Username: `guest`  
Password: `guest`

# After all stop docker compose
```sh
make prod_down
```