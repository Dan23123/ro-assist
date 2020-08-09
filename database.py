import psycopg2
from config import DATABASE_URL

db = psycopg2.connect(DATABASE_URL)
db.autocommit = True
cursor = db.cursor()

cursor.execute("""
	CREATE TABLE IF NOT EXISTS guilds (
		guild_id BIGINT PRIMARY KEY,
		prefix VARCHAR(1) DEFAULT '!',
		verification_channel_id BIGINT,
		verification_role_id BIGINT,
		verification_set_username BOOLEAN,
		muted_role_id BIGINT,
		suggestion_channel_id BIGINT
	);

	CREATE TABLE IF NOT EXISTS users (
		user_id BIGINT PRIMARY KEY,
		level BIGINT DEFAULT 1 NOT NULL,
		exp BIGINT DEFAULT 0 NOT NULL,
		robux BIGINT DEFAULT 0 NOT NULL,
		roblox_id BIGINT DEFAULT NULL,
		job_id SMALLINT DEFAULT NULL,
		inventory TEXT DEFAULT '[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]' NOT NULL,
		daily_reward_time BIGINT
	);

	CREATE TABLE IF NOT EXISTS giveaways (
		guild_id BIGINT NOT NULL,
		channel_id BIGINT NOT NULL,
		message_id BIGINT NOT NULL,
		reward VARCHAR(50) NOT NULL,
		winners SMALLINT NOT NULL,
		requirements TEXT DEFAULT '' NOT NULL,
		ends_at BIGINT NOT NULL,
		ended BOOLEAN DEFAULT false NOT NULL
	);

	ALTER TABLE users 
	ADD COLUMN daily_reward_time BIGINT;
""")
# db.commit()

def add_guild(guild_id):
	cursor.execute("INSERT INTO guilds (guild_id) VALUES (%s);", (guild_id,))
	# db.commit()

def get_guild(guild_id):
	cursor.execute("SELECT * FROM guilds WHERE guild_id = %s;", (guild_id,))
	result = cursor.fetchone()

	if result == None:
		add_guild(guild_id)
		result = get_guild(guild_id)

	return result

def add_user(user_id):
	cursor.execute("INSERT INTO users (user_id) VALUES (%s);", (user_id,))
	# db.commit()

def get_user(user_id):
	cursor.execute("SELECT * FROM users WHERE user_id = %s;", (user_id,))
	result = cursor.fetchone()

	if result == None:
		add_user(user_id)
		result = get_user(user_id)

	return result

def get_all_users():
	cursor.execute("SELECT * FROM users;")
	return cursor.fetchall()

def get_top10_users(order_by, limit):
	cursor.execute(f"SELECT * FROM users ORDER BY {order_by} DESC LIMIT 10;")
	return cursor.fetchall()

def add_giveaway(guild_id, channel_id, message_id, reward, winners, requirements, ends_at):
	cursor.execute("INSERT INTO giveaways (guild_id, channel_id, message_id, reward, winners, requirements, ends_at) VALUES (%s, %s, %s, %s, %s, %s, %s);", (guild_id, channel_id, message_id, reward, winners, requirements, ends_at,))
	# db.commit()

def get_giveaway(guild_id, channel_id, message_id):
	cursor.execute("SELECT * FROM giveaways WHERE guild_id = %s AND channel_id = %s AND message_id = %s;", (guild_id, channel_id, message_id,))
	return cursor.fetchone()

def get_all_giveaways():
	cursor.execute("SELECT * FROM giveaways;")
	return cursor.fetchall()

def get_guild_giveaways(guild_id):
	cursor.execute("SELECT * FROM giveaways WHERE guild_id = %s;", (guild_id,))
	return cursor.fetchall()

def delete_giveaway(guild_id, channel_id, message_id):
	cursor.execute("DELETE FROM giveaways WHERE guild_id = %s AND channel_id = %s AND message_id = %s", (guild_id, channel_id, message_id,))
	# db.commit()