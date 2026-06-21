package org.webservices.testrunner.suites

import io.ktor.client.request.*
import io.ktor.http.ContentType
import io.ktor.http.HttpStatusCode
import io.ktor.http.contentType
import org.webservices.testrunner.framework.*

suspend fun TestRunner.ntfyExtendedCommunicationTests() = suite("Ntfy Extended Communication Tests") {
test("Ntfy: Topics can be created") {
        require(endpoints.ntfy != null) { "Ntfy endpoint not configured" }

        val testTopic = "test-topic-${System.currentTimeMillis()}"
        val response = client.getRawResponse("${endpoints.ntfy}/$testTopic")

        response.status shouldBe HttpStatusCode.OK
        println("      ✓ Topic endpoint accessible")
    }

    test("Ntfy: Message publishing endpoint") {
        require(endpoints.ntfy != null) { "Ntfy endpoint not configured" }

        val testTopic = "test-integration-${System.currentTimeMillis()}"

        try {
            val response = httpClient.post("${endpoints.ntfy}/$testTopic") {
                basicAuth(
                    System.getenv("NTFY_USERNAME").orEmpty(),
                    System.getenv("NTFY_PASSWORD").orEmpty()
                )
                setBody("Test message from integration tests")
            }

            response.status shouldBe HttpStatusCode.OK
            println("      ✓ Message publishing successful")
        } catch (e: Exception) {
            fail("Ntfy message publishing failed: ${e.message}")
        }
    }

    test("Ntfy: JSON API endpoint") {
        require(endpoints.ntfy != null) { "Ntfy endpoint not configured" }

        val testTopic = "test-json-${System.currentTimeMillis()}"

        try {
            val response = httpClient.post("${endpoints.ntfy}/$testTopic") {
                basicAuth(
                    System.getenv("NTFY_USERNAME").orEmpty(),
                    System.getenv("NTFY_PASSWORD").orEmpty()
                )
                contentType(ContentType.Application.Json)
                setBody("""{"message":"Test from integration","title":"Integration Test"}""")
            }

            response.status shouldBe HttpStatusCode.OK
            println("      ✓ JSON API functional")
        } catch (e: Exception) {
            fail("Ntfy JSON API check failed: ${e.message}")
        }
    }
}
