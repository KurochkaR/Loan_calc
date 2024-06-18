# How to run a project on your local machine?
1. Install Docker https://docs.docker.com/engine/install/
2. Rename file example to .env
3. Run docker-compose up --build
4. Run migrations by docker exec -it web_payments python3 manage.py migrate
5. Send POST to http://localhost/api/loans/ for creating loan and payments schedule
   - example of json:
     - {
         "amount": 1000,
         "loan_start_date": "10-01-2024",
         "number_of_payments": 4,
         "periodicity": "1m",
         "interest_rate": 0.1
     }
6. At http://localhost/api/loans/1/payments you can see list of payments for this loan(in example - loan with id 1)
7. Send PUT to http://localhost/api/payments/2/ for change principal and recalculate further payments (in example - change payment with id 2)
   - example of json:
     - { "principal": 50 }
8. Run tests using command docker exec -it web_payments python3 manage.py test