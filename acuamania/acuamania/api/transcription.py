import frappe


LOGGER_NAME = "acuamania.transcription"


import frappe


LOGGER_NAME = "acuamania.transcription"


@frappe.whitelist(methods=["POST"])
def append_transcription():
	"""
	Append a text snippet to Contact.custom_transcription_text.
	"""

	logger = frappe.logger(LOGGER_NAME)
	logger.debug("append_transcription: start")

	data = frappe.local.form_dict or {}
	logger.debug(
		"Request payload extracted",
		extra={"has_data": bool(data)}
	)

	phone = data.get("phone")
	message = data.get("message")

	logger.debug(
		"Request parameters resolved",
		extra={
			"has_phone": bool(phone),
			"has_message": bool(message),
			"message_length": len(message) if message else 0,
		}
	)

	try:
		logger.debug("Validating input")
		validate_input(phone, message)
		logger.debug("Input validation passed")

		logger.debug("Resolving contact by phone")
		contact_name = find_contact_by_phone(phone)

		logger.debug(
			"Contact lookup completed",
			extra={
				"phone": phone,
				"contact_found": bool(contact_name),
				"contact": contact_name,
			}
		)

		if not contact_name:
			logger.info(
				"Transcription ignored: contact not found",
				extra={"phone": phone}
			)
			return ignored_response()

		logger.debug("Loading Contact document")
		contact = frappe.get_doc("Contact", contact_name)

		logger.debug(
			"Contact document loaded",
			extra={
				"contact": contact.name,
				"has_existing_buffer": bool(contact.custom_transcription_text),
				"existing_buffer_length": (
					len(contact.custom_transcription_text)
					if contact.custom_transcription_text else 0
				),
			}
		)

		logger.debug("Sanitizing incoming message")
		cleaned_message = sanitize_message(message)

		logger.debug(
			"Message sanitized",
			extra={"cleaned_message_length": len(cleaned_message)}
		)

		logger.debug("Building updated transcription buffer")
		updated_buffer = build_updated_buffer(
			contact.custom_transcription_text,
			cleaned_message
		)

		logger.debug(
			"Updated buffer built",
			extra={
				"new_buffer_length": len(updated_buffer),
				"delta_length": (
					len(updated_buffer)
					- (len(contact.custom_transcription_text or ""))
				),
			}
		)

		logger.debug("Assigning buffer to Contact")
		contact.custom_transcription_text = updated_buffer

		logger.debug("Saving Contact document")
		contact.save(ignore_permissions=True)

		logger.info(
			"Transcription appended successfully",
			extra={
				"contact": contact.name,
				"phone": phone,
				"buffer_length": len(updated_buffer),
			}
		)

		logger.debug("append_transcription: end (success)")
		return success_response(contact.name, len(updated_buffer))

	except frappe.ValidationError:
		logger.warning(
			"Validation error while appending transcription",
			extra={"phone": phone}
		)
		raise

	except Exception:
		logger.error(
			"Unhandled exception in append_transcription",
			extra={"phone": phone},
			exc_info=True
		)
		raise


def validate_input(phone: str, message: str):
	if not phone or not message:
		frappe.throw("Both 'phone' and 'message' are required.")


def find_contact_by_phone(phone: str) -> str | None:
	return frappe.db.get_value(
		"Contact Phone",
		{"phone": phone},
		"parent"
	)


def sanitize_message(msg: str) -> str:
	return str(msg).replace("\r", " ").strip()


def build_updated_buffer(existing: str, new: str) -> str:
	if existing:
		return f"{existing}\n{new}"
	return new


def ignored_response():
	return {
		"status": "ignored",
		"reason": "Contact not found for this phone",
	}


def success_response(contact_name: str, length: int):
	return {
		"status": "success",
		"contact": contact_name,
		"buffer_length": length,
	}
