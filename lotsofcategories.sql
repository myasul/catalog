-- INSERT INTO table_name
-- VALUES (value1, value2, value3, ...);


-- Test Categories
INSERT INTO categories (name, user_id) VALUES ('Anime', 1);
INSERT INTO categories (name, user_id) VALUES ('Manga', 1);
INSERT INTO categories (name, user_id) VALUES( 'Novels', 1);

-- Test User

INSERT INTO users (name, email, image) 
    VALUES ('Test User', 'test_user@test.com', 'blank_face.jpg');

-- Test Item
    INSERT INTO items (name, description, image, category_id, user_id)
        VALUES ('One Piece', E'One Piece (Japanese: ワンピース Hepburn: Wan Pīsu) is a Japanese manga series written and illustrated by Eiichiro Oda. It has been serialized in Shueisha\'s Weekly Shōnen Jump magazine since July 22, 1997, and has been collected in 88 tankōbon volumes. The story follows the adventures of Monkey D. Luffy, a boy whose body gained the properties of rubber after unintentionally eating a Devil Fruit. With his crew of pirates, named the Straw Hat Pirates, Luffy explores the Grand Line in search of the world\'s ultimate treasure known as \'One Piece\' in order to become the next Pirate King.', 'test_image.jpg', 3, 1);


-- Alter Item
ALTER TABLE items
    ALTER COLUMN description TYPE VARCHAR(1000);