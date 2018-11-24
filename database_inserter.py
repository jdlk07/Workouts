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

bodypart1 = BodyParts(name = "Chest")
session.add(bodypart1)
session.commit()

bodypart2 = BodyParts(name = "Forearms")
session.add(bodypart2)
session.commit()

bodypart3 = BodyParts(name = "Lats")
session.add(bodypart3)
session.commit()

bodypart4 = BodyParts(name = "Quadriceps")
session.add(bodypart4)
session.commit()

bodypart5 = BodyParts(name = "Hamstrings")
session.add(bodypart5)
session.commit()

bodypart6 = BodyParts(name = "Calves")
session.add(bodypart6)
session.commit()

bodypart7 = BodyParts(name = "Triceps")
session.add(bodypart7)
session.commit()

bodypart8 = BodyParts(name = "Traps")
session.add(bodypart8)
session.commit()

bodypart9 = BodyParts(name = "Shoulders")
session.add(bodypart9)
session.commit()

bodypart10 = BodyParts(name = "Abdominals")
session.add(bodypart10)
session.commit()

bodypart11 = BodyParts(name = "Glutes")
session.add(bodypart11)
session.commit()

bodypart12 = BodyParts(name = "Biceps")
session.add(bodypart12)
session.commit()

# exercise1 = Exercises(name = "Bench Press", description = "Basic Chest Exercise", bodyPart_id = 1)
# session.add(exercise1)
# session.commit()


print "Database has been populated"
