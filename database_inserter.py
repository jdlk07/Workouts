from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import BodyParts, Base, Exercises

engine = create_engine('sqlite:///exercises.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine


DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# bodypart1 = BodyParts(name = "Chest")
# session.add(bodypart1)
# session.commit()
#
# bodypart2 = BodyParts(name = "Forearms")
# session.add(bodypart2)
# session.commit()
#
# bodypart3 = BodyParts(name = "Lats")
# session.add(bodypart3)
# session.commit()
#
# bodypart4 = BodyParts(name = "Quadriceps")
# session.add(bodypart4)
# session.commit()
#
# bodypart5 = BodyParts(name = "Hamstrings")
# session.add(bodypart5)
# session.commit()
#
# bodypart6 = BodyParts(name = "Calves")
# session.add(bodypart6)
# session.commit()
#
# bodypart7 = BodyParts(name = "Triceps")
# session.add(bodypart7)
# session.commit()
#
# bodypart8 = BodyParts(name = "Traps")
# session.add(bodypart8)
# session.commit()
#
# bodypart9 = BodyParts(name = "Shoulders")
# session.add(bodypart9)
# session.commit()
#
# bodypart10 = BodyParts(name = "Abdominals")
# session.add(bodypart10)
# session.commit()
#
# bodypart11 = BodyParts(name = "Glutes")
# session.add(bodypart11)
# session.commit()
#
# bodypart12 = BodyParts(name = "Biceps")
# session.add(bodypart12)
# session.commit()

exercise1 = Exercise(name = "Squat", description = "Performed by squatting down with a weight held across the upper back under neck and standing up straight again. This is a compound exercise that also involves the glutes (buttocks) and, to a lesser extent, the hamstrings, calves, and the lower back. Lifting belts are sometimes used to help support the lower back. The freeweight squat is one of 'The Big Three' powerlifting exercises, along with the deadlift and the bench press.", bodyPart_id = 4, user_id = 1)
session.add(exercise1)
session.commit()

exercise2 = Exercise(name = "Leg Press", description = "Performed while seated by pushing a weight away from the body with the feet. It is a compound exercise that also involves the glutes and, to a lesser extent, the hamstrings and the calves. Overloading the machine can result in serious injury if the sled moves uncontrollably towards the trainer.[", bodyPart_id = 4, user_id = 3)
session.add(exercise2)
session.commit()

exercise3 = Exercise(name = "Deadlift", description = "Performed by squatting down and lifting a weight off the floor with the hand until standing up straight again. Grips can be face down or opposing with one hand down and one hand up, to prevent dropping. Face up should not be used because this puts excess stress on the inner arms. This is a compound exercise that also involves the glutes, lower back, lats, trapezius (neck) and, to a lesser extent, the hamstringcacas and the calves. Lifting belts are often used to help support the lower back. The deadlift has two common variants, the Romanian deadlift and the straight-leg-deadlift. Each target the lower back, glutes and the hamstrings differently.", bodyPart_id = 4, user_id = 2)
session.add(exercise3)
session.commit()

exercise4 = Exercise(name = "Leg Extensions", description = "Performed while seated by raising a weight out in front of the body with the feet. It is an isolation exercise for the quadriceps. Overtraining can cause patellar tendinitis.[4] The legs extension serves to also strengthen the muscles around the knees and is an exercise that is preferred by physical therapists.", bodyPart_id = 4, user_id = 2)
session.add(exercise4)
session.commit()

exercise5 = Exercise(name = "Leg Curl", description = "Performed while lying face down on a bench, by raising a weight with the feet towards the buttocks. This is an isolation exercise for the hamstrings", bodyPart_id = 5, user_id = 1)
session.add(exercise5)
session.commit()

exercise6 = Exercise(name = "Stiff-Legged Deadlift", description = "The Stiff-Legged Deadlift is a deadlift variation that specifically targets the posterior chain. Little to no knee movement occurs in this exercise to ensure hamstring, glute, and spinal erector activation. The bar starts on the floor and the individual sets up like a normal deadlift but the knees are at a 160° angle instead on 135° on the conventional deadlift.", bodyPart_id = 5, user_id = 1)
session.add(exercise6)
session.commit()

exercise7 = Exercise(name = "Standing Calf Raise", description = "The standing calf raise is performed by plantarflexing the feet to lift the body. If a weight is used, then it rests upon the shoulders, or is held in the hand(s). This is an isolation exercise for the calves; it particularly emphasises the gastrocnemius muscle, and recruits the soleus muscle", bodyPart_id = 6, user_id = 1)
session.add(exercise7)
session.commit()

exercise8 = Exercise(name = "Seated Calf Raise", description = "The seated calf raise is performed by flexing the feet to lift a weight held on the knees. This is an isolation exercise for the calves, and particularly emphasises the soleus muscle.", bodyPart_id = 6, user_id = 1)
session.add(exercise8)
session.commit()

exercise9 = Exercise(name = "Bent Over Rows", description = "The bent-over row is performed while leaning over, holding a weight hanging down in one hand or both hands, by pulling it up towards the abdomen. This is a compound exercise that also involves the biceps, forearms, traps, and the rear deltoids. The torso is unsupported in some variants of this exercise, in which case lifting belts are often used to help support the lower back.", bodyPart_id = 3, user_id = 3)
session.add(exercise9)
session.commit()

exercise10 = Exercise(name = "Upright Rows", description = "The upright row is performed while standing, holding a weight hanging down in the hands, by lifting it straight up to the collarbone. This is a compound exercise that also involves the trapezius, upper back, forearms, triceps, and the biceps. The narrower the grip the more the trapezius muscles are exercised.", bodyPart_id = 8, user_id = 1)
session.add(exercise10)
session.commit()

exercise11 = Exercise(name = "Shoulder Press", description = "The shoulder press is performed while seated, or standing by lowering a weight held above the head to just above the shoulders, and then raising it again. It can be performed with both arms, or one arm at a time. This is a compound exercise that also involves the trapezius and the triceps.", bodyPart_id = 9, user_id = 1)
session.add(exercise11)
session.commit()

exercise12 = Exercise(name = "Lateral Raise", description = "The lateral raise (or shoulder fly) is performed while standing or seated, with hands hanging down holding weights, by lifting them out to the sides until just below the level of the shoulders. A slight variation in the lifts can hit the deltoids even harder, while moving upwards, just turn the hands slightly downwards, keeping the last finger higher than the thumb. This is an isolation exercise for the deltoids. Also works the forearms and traps.", bodyPart_id = 9, user_id = 1)
session.add(exercise12)
session.commit()

exercise13 = Exercise(name = "Tricep Pushdowns", description = "The pushdown is performed while standing by pushing down on a bar held at the level of the upper chest. It is important to keep the elbows at shoulder width and in line with shoulder/legs. In other words, elbows position should not change while moving the forearm pushes down the bar. This is an isolation exercise for the triceps.", bodyPart_id = 7, user_id = 2)
session.add(exercise13)
session.commit()

exercise14 = Exercise(name = "Tricep Extension", description = "The triceps extension is performed while standing or seated, by lowering a weight held above the head (keeping the upper arms motionless), and then raising it again. It can be performed with both arms, or one arm at a time. This is an isolation exercise for the triceps. It is also known as the french curl.", bodyPart_id = 7, user_id = 3)
session.add(exercise14)
session.commit()

exercise15 = Exercise(name = "Preacher Curls", description = "The Preacher curl is performed while standing or seated, with hands hanging down holding weights (palms facing forwards), by curling them up to the shoulders. It can be performed with both arms, or one arm at a time.", bodyPart_id = 12, user_id = 2)
session.add(exercise15)
session.commit()


# exercise1 = Exercises(name = "Bench Press", description = "Basic Chest Exercise", bodyPart_id = 1)
# session.add(exercise1)
# session.commit()


print "Database has been populated"
