db = db.getSiblingDB("subscribers_db");
db.subscription_table.drop();

db.subscription_table.insertMany([
    {
        "username": "Dale",
        "owner": "Test",
        "repo": "Repo"
    },
]);