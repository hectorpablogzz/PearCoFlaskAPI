from supabase import create_client, Client

def caficultores_json(supabase):
    
    response = supabase.table("caficultores").select("*").execute()
    return {"results": response.data}

def add_caficultor(supabase, new_caficultor):
    try:
        # The schema specifies 'telephone' and 'email' as nullable.
        # If they are empty strings in the payload, they should be converted to None
        # to be inserted as NULL in the database.
        telephone = new_caficultor.get('telephone')
        if telephone == '':
            telephone = None
            
        email = new_caficultor.get('email')
        if email == '':
            email = None

        caficultor_data = {
            'id': new_caficultor.get('id'),
            'name': new_caficultor.get('name'),
            'lastname': new_caficultor.get('lastname'),
            'gender': new_caficultor.get('gender'),
            'telephone': telephone,
            'email': email,
            'address': new_caficultor.get('address'),
            'birthDate': new_caficultor.get('birthDate')
        }
        
        response = supabase.table('caficultores').insert(caficultor_data).execute()

        if response.data:
            return {"success": True, "message": "Caficultor agregado exitosamente", "data": response.data}, 201
        
        if response.error:
            return {"success": False, "message": response.error.message}, 400
        
        return {"success": False, "message": "Error desconocido"}, 500

    except Exception as e:
        return {"success": False, "message": str(e)}, 500

def edit_caficultor(supabase, caficultor_id, data):
    try:
        update_data = data.copy()

        # Remove id from data if it exists, as we don't want to update the primary key
        update_data.pop('id', None)

        # Handle nullable fields that might be empty strings
        if 'telephone' in update_data and update_data['telephone'] == '':
            update_data['telephone'] = None
        if 'email' in update_data and update_data['email'] == '':
            update_data['email'] = None

        # Ensure there is data to update
        if not update_data:
            return {"success": False, "message": "No data provided for update"}, 400

        response = supabase.table('caficultores').update(update_data).eq('id', caficultor_id).execute()

        if response.data:
            return {"success": True, "message": "Caficultor actualizado exitosamente", "data": response.data}, 200
        
        if response.error:
            return {"success": False, "message": response.error.message}, 400
        
        # If data is empty and there is no error, it means no row was found to update.
        return {"success": False, "message": f"No se encontró un caficultor con el id {caficultor_id}"}, 404

    except Exception as e:
        return {"success": False, "message": str(e)}, 500

def delete_caficultor(supabase, id):
    try:
        response = supabase.table('caficultores').delete().eq('id', id).execute()

        if response.data:
            return {"success": True, "message": "Caficultor eliminado exitosamente"}, 200
        
        if response.error:
            return {"success": False, "message": response.error.message}, 400
        
        # If data is empty and there is no error, it means no row was found to delete.
        return {"success": False, "message": f"No se encontró un caficultor con el id {id}"}, 404

    except Exception as e:
        return {"success": False, "message": str(e)}, 500