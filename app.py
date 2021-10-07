import mariadb
from flask import Flask, request, Response
import dbcreds
import json
import sys

app = Flask(__name__)

@app.route('/api/posts', methods=['GET', 'POST', 'PATCH', 'DELETE'])
def handler():
    try:
        conn = mariadb.connect(
                        user=dbcreds.user,
                        password=dbcreds.password,
                        host=dbcreds.host,
                        port=dbcreds.port,
                        database=dbcreds.database
                        )
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute("SELECT * from posts")
            all_content = cursor.fetchall()
            print(all_content)
            return Response(json.dumps(all_content), mimetype="application/json", status=200)
            
        elif request.method == 'POST':
            data = request.json

            if len(data) == 1 and {"content"} <= data.keys():
                content = data.get("content")
                cursor.execute("INSERT INTO posts(content) VALUES(?)", [content])
                conn.commit()
                
                cursor.execute("SELECT * FROM posts WHERE content=?", [content])
                current_post = cursor.fetchone()

                resp = {
                    "id": current_post[0],
                    "content": current_post[1]
                }

                return Response(json.dumps(resp), mimetype="application/json", status=200)
            else:
                print("Invalid json request")
                return Response("Invalid request", mimetype="text/plain", status=400)

        elif request.method == 'PATCH':
            data = request.json

            if len(data) == 2 and {"id", "content"} <= data.keys():
                post_id = data.get("id")
                new_content = data.get("content")

                cursor.execute("SELECT EXISTS(SELECT * FROM posts WHERE id=?)", [post_id])
                check_exists = cursor.fetchone()[0]
                if check_exists == 1:
                    cursor.execute("UPDATE posts SET content=? WHERE id=?", [new_content, post_id])
                    conn.commit()
                    return Response("Success", mimetype="text/plain", status=200)
                else:
                    print("not a valid post id")
                    return Response("That post id does not exist", mimetype="text/plain", status=400)
            else:
                print("Invalid Json data")
                return Response("Invalid Json Data", mimetype="text/plain", status=200)
            
        elif request.method == 'DELETE':
            data = request.json

            if len(data) == 1 and {"id"} <= data.keys():
                post_id = data.get("id")

                cursor.execute("SELECT EXISTS(SELECT * FROM posts WHERE id=?)", [post_id])
                check_exists = cursor.fetchone()[0]
                if check_exists == 1:
                    cursor.execute("DELETE FROM posts WHERE id=?", [post_id])
                    conn.commit()
                    return Response("Deleted", mimetype="text/plain", status=200)
                else:
                    print("not a valid post id")
                    return Response("That post id does not exist", mimetype="text/plain", status=400)
            else:
                print("Invalid Json data")
                return Response("Invalid Json Data", mimetype="text/plain", status=200)

        else:
            print("Something went wronng, Bad request method")

    except mariadb.DataError:
        print("Something is wrong with your data")
        return Response("Something is wrong with the data", status=404)
    except mariadb.OperationalError:
        print("Something is wrong with your connection")
        return Response("Something is wrong with the connection", status=500)
    except:
        print("Something went wrong")
        return Response("Something went wrong", status=500)
    finally:
        if (cursor != None):
            cursor.close()
        if (conn != None):
            conn.rollback()
            conn.close()


if len(sys.argv) > 1 and len(sys.argv) < 3:
    mode = sys.argv[1]
    if mode == "production":
        import bjoern
        host = "0.0.0.0"
        port = 5000
        print("Running in production mode")
        bjoern.run(app, host, port)
    elif mode == "testing":
        from flask_cors import CORS
        CORS(app)
        print("Running in testing mode")
        #debug=True ONLY EVER used behind testing mode. Do not allow debug=True on production server.
        app.run(debug=True)
    else:
        print("Invalid mode argument. Please choose testing or production")  

else:
    print("No argument provided or too many arguments")
    exit()
